#!/usr/bin/env python3
"""langstats: measure which languages Claude Code works in and publish the
result as a text-bar block in a GitHub profile README.

Subcommands:
    hook            PostToolUse hook: reads the payload on stdin, appends a heartbeat
    session-start   SessionStart hook: data migration and retention cleanup
    session-end     SessionEnd hook: launches a detached auto-publish when due
    stats           print the language table for the configured range
    publish         rewrite the README section (git clone, GitHub API via gh, or
                    print the block to paste by hand when GitHub is not connected)
    snippet         print the README block with its markers, ready to paste
    config          show / set / unset / path
    doctor          check that the configuration is ready to publish
    insert-markers  append the section markers to the README

Runtime: Python 3.9+, standard library only. Hook subcommands never fail the
session: any error goes to stderr and the process exits with code 0. The hook
path imports as little as possible (no argparse, no subprocess) because it runs
after every Read/Edit.
"""

from __future__ import annotations

import sys

MIN_PYTHON = (3, 9)

if sys.version_info < MIN_PYTHON:  # pragma: no cover - checked before anything else
    sys.stderr.write(
        "langstats: Python %d.%d+ is required (found %d.%d); nothing was recorded.\n"
        % (MIN_PYTHON + sys.version_info[:2])
    )
    sys.exit(0)

import datetime as dt  # noqa: E402
import fnmatch  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

TYPE_CHECKING = False  # avoids importing typing on the hook path

if TYPE_CHECKING:  # pragma: no cover
    import argparse
    from typing import Any, Callable

# argparse, base64, shutil and subprocess are imported lazily where needed so
# the PostToolUse hook stays fast.

__version__ = "0.2.0"

SCHEMA_VERSION = 1
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
LANGUAGES_FILE = SCRIPT_DIR / "languages.json"

TRACKED_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit", "Read")
OTHER = "Other"
SETUP_HINT = "Run /langstats:setup to configure it."
MODES = ("auto", "git", "gh", "manual")
SNIPPET_FILE = "readme-snippet.md"
HEARTBEAT_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")

DEFAULTS: dict[str, Any] = {
    "mode": "auto",
    "readme_repo_path": None,
    "readme_repo": None,
    "readme_file": "README.md",
    "section": "langstats",
    "range_days": 7,
    "top_n": 7,
    "min_percent": 0.5,
    "blocks": "░▒▓█",
    "bar_length": 25,
    "name_width": 32,
    "show_time": False,
    "show_title": False,
    "timeout_minutes": 15,
    "track_reads": True,
    "exclude_languages": [],
    "language_overrides": {},
    "ignore_globs": [".claude", "node_modules", ".git", "vendor", "dist", ".venv"],
    "auto_publish": False,
    "publish_interval_hours": 12,
    "commit_message": "chore(readme): update language stats",
    "retention_days": 365,
}


class LangstatsError(Exception):
    """An error with a message meant for the user."""


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _str_list(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


# key -> (kind, check, human readable rule). kind drives `config set` parsing.
SCHEMA: dict[str, tuple[str, Callable[[Any], bool], str]] = {
    "mode": ("str", lambda v: v in MODES, '"auto", "git", "gh" or "manual"'),
    "readme_repo_path": ("nstr", lambda v: v is None or _nonempty_str(v), "a path or null"),
    "readme_repo": (
        "nstr",
        lambda v: v is None or (isinstance(v, str) and re.fullmatch(r"[\w.-]+/[\w.-]+", v) is not None),
        '"owner/repo" or null',
    ),
    "readme_file": ("str", _nonempty_str, "a non-empty file name"),
    "section": (
        "str",
        lambda v: isinstance(v, str) and re.fullmatch(r"[\w.-]+", v) is not None,
        "letters, digits, '_', '-' or '.'",
    ),
    "range_days": ("int", lambda v: _is_int(v) and v >= 0, "an integer >= 0 (0 = all)"),
    "top_n": ("int", lambda v: _is_int(v) and v >= 1, "an integer >= 1"),
    "min_percent": ("num", lambda v: _is_num(v) and 0 <= v <= 100, "a number between 0 and 100"),
    "blocks": ("str", lambda v: isinstance(v, str) and len(v) >= 2, "a string of at least 2 characters"),
    "bar_length": ("int", lambda v: _is_int(v) and 1 <= v <= 200, "an integer between 1 and 200"),
    "name_width": ("int", lambda v: _is_int(v) and 1 <= v <= 200, "an integer between 1 and 200"),
    "show_time": ("bool", lambda v: isinstance(v, bool), "true or false"),
    "show_title": ("bool", lambda v: isinstance(v, bool), "true or false"),
    "timeout_minutes": ("num", lambda v: _is_num(v) and v > 0, "a number > 0"),
    "track_reads": ("bool", lambda v: isinstance(v, bool), "true or false"),
    "exclude_languages": ("list", _str_list, "a list of language names"),
    "language_overrides": (
        "dict",
        lambda v: isinstance(v, dict) and all(isinstance(k, str) and _nonempty_str(x) for k, x in v.items()),
        'an object like {".foo": "Language"}',
    ),
    "ignore_globs": ("list", _str_list, "a list of glob patterns"),
    "auto_publish": ("bool", lambda v: isinstance(v, bool), "true or false"),
    "publish_interval_hours": ("num", lambda v: _is_num(v) and v >= 0, "a number >= 0"),
    "commit_message": ("str", _nonempty_str, "a non-empty string"),
    "retention_days": ("int", lambda v: _is_int(v) and v >= 0, "an integer >= 0 (0 = keep forever)"),
}

assert set(SCHEMA) == set(DEFAULTS)


def warn(msg: str) -> None:
    sys.stderr.write("langstats: %s\n" % msg)


def langstats_home() -> Path:
    return Path(os.environ.get("LANGSTATS_HOME") or "~/.claude/langstats").expanduser()


def legacy_home() -> Path:
    return Path(os.environ.get("LANGTIME_HOME") or "~/.claude/langtime").expanduser()


def config_path(home: Path) -> Path:
    return home / "config.json"


def read_user_config(home: Path) -> dict[str, Any]:
    """The raw contents of config.json ({} if missing). Raises on bad JSON."""
    path = config_path(home)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config.json must contain a JSON object")
    return data


def validate_config(user: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Merge user values over the defaults. Invalid or unknown keys are dropped
    (the default is kept) and reported in the returned problem list."""
    cfg = json.loads(json.dumps(DEFAULTS))  # deep copy
    problems = []
    for key, value in user.items():
        if key not in SCHEMA:
            problems.append("unknown config key %r (ignored)" % key)
            continue
        _, check, rule = SCHEMA[key]
        if not check(value):
            problems.append("invalid value for %r: %s; expected %s (using default)" % (key, json.dumps(value), rule))
            continue
        cfg[key] = value
    return cfg, problems


def load_config(home: Path, report: bool = True) -> dict[str, Any]:
    """Never raises: a broken config falls back to the defaults with a warning."""
    try:
        user = read_user_config(home)
    except (OSError, ValueError) as exc:
        if report:
            warn("could not read %s: %s (using defaults)" % (config_path(home), exc))
        user = {}
    cfg, problems = validate_config(user)
    if report:
        for p in problems:
            warn(p)
    return cfg


def parse_config_value(key: str, raw: str) -> Any:
    if key not in SCHEMA:
        raise LangstatsError("unknown config key %r. Known keys: %s" % (key, ", ".join(sorted(SCHEMA))))
    kind, check, rule = SCHEMA[key]
    text = raw.strip()
    try:
        if kind == "nstr" and text.lower() in ("null", "none", ""):
            value: Any = None
        elif kind in ("str", "nstr"):
            value = raw
        elif kind == "bool":
            low = text.lower()
            if low in ("true", "yes", "on", "1"):
                value = True
            elif low in ("false", "no", "off", "0"):
                value = False
            else:
                raise ValueError(raw)
        elif kind == "int":
            value = int(text)
        elif kind == "num":
            number = float(text)
            value = int(number) if number.is_integer() else number
        elif kind == "list":
            if text.startswith("["):
                value = json.loads(text)
            else:
                value = [x.strip() for x in text.split(",") if x.strip()]
        elif kind == "dict":
            value = json.loads(text)
        else:  # pragma: no cover
            raise ValueError(kind)
    except ValueError:
        raise LangstatsError("invalid value for %r: %r; expected %s" % (key, raw, rule)) from None
    if not check(value):
        raise LangstatsError("invalid value for %r: %r; expected %s" % (key, raw, rule))
    return value


def write_user_config(home: Path, data: dict[str, Any]) -> None:
    home.mkdir(parents=True, exist_ok=True)
    tmp = config_path(home).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(config_path(home)))


# --------------------------------------------------------------------------- #
# Home directory, migration, state
# --------------------------------------------------------------------------- #


def migrate_legacy(home: Path) -> bool:
    """Copy ~/.claude/langtime (v0.1.0) into the langstats home, once: only when
    the destination holds no data yet (no config, no heartbeats)."""
    if (home / "heartbeats").exists() or (home / "config.json").exists():
        return False
    if (home / ".migrated-from-langtime").exists():
        return False
    legacy = legacy_home()
    if not legacy.is_dir():
        return False
    import shutil

    try:
        home.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(legacy), str(home), dirs_exist_ok=True)
        (home / ".migrated-from-langtime").write_text(str(legacy) + "\n", encoding="utf-8")
    except OSError as exc:
        warn("could not migrate %s to %s: %s" % (legacy, home, exc))
        return False
    warn("migrated data from %s to %s" % (legacy, home))
    return True


def prepare_home() -> Path:
    home = langstats_home()
    migrate_legacy(home)
    return home


def heartbeats_dir(home: Path) -> Path:
    return home / "heartbeats"


def state_path(home: Path) -> Path:
    return home / "state.json"


def read_state(home: Path) -> dict[str, Any]:
    try:
        data = json.loads(state_path(home).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def update_state(home: Path, **values: Any) -> None:
    state = read_state(home)
    state.update(values)
    home.mkdir(parents=True, exist_ok=True)
    tmp = state_path(home).with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(state_path(home)))


# --------------------------------------------------------------------------- #
# Language detection
# --------------------------------------------------------------------------- #

_LANGUAGES_CACHE: dict[str, Any] | None = None


def load_languages() -> dict[str, Any]:
    global _LANGUAGES_CACHE
    if _LANGUAGES_CACHE is None:
        _LANGUAGES_CACHE = json.loads(LANGUAGES_FILE.read_text(encoding="utf-8"))
    return _LANGUAGES_CACHE


def basename(path: str) -> str:
    return re.split(r"[\\/]", path.rstrip("\\/"))[-1]


def _extension(name: str) -> str:
    stem, ext = os.path.splitext(name)
    return ext if stem else ""


def _shebang_language(path: str, shebangs: dict[str, str]) -> str | None:
    try:
        with open(path, "rb") as fh:
            first = fh.readline(256)
    except OSError:
        return None
    if not first.startswith(b"#!"):
        return None
    parts = first[2:].decode("utf-8", "replace").split()
    if not parts:
        return None
    interp = basename(parts[0])
    if interp == "env":
        rest = [p for p in parts[1:] if not p.startswith("-") and "=" not in p]
        if not rest:
            return None
        interp = rest[0]
    for candidate in (interp, interp.rstrip("0123456789."), re.sub(r"[\d.]+$", "", interp)):
        if candidate in shebangs:
            return shebangs[candidate]
    return None


def detect_language(path: str, overrides: dict[str, str] | None = None, languages: dict[str, Any] | None = None) -> str:
    """Priority: overrides > exact file name > compound prefix/suffix > extension
    > shebang (only without extension) > Other."""
    langs = languages or load_languages()
    name = basename(path)
    lower = name.lower()
    ext = _extension(name)

    for key, lang in (overrides or {}).items():
        if key == name:
            return lang
    for key, lang in (overrides or {}).items():
        norm = key if key.startswith(".") else "." + key
        if ext and norm.lower() == ext.lower():
            return lang

    filenames = langs.get("filenames", {})
    if name in filenames:
        return filenames[name]
    for fname, lang in filenames.items():
        if fname.lower() == lower:
            return lang

    for prefix, lang in sorted(langs.get("prefixes", {}).items(), key=lambda kv: -len(kv[0])):
        if name.startswith(prefix):
            return lang
    for suffix, lang in sorted(langs.get("suffixes", {}).items(), key=lambda kv: -len(kv[0])):
        if lower.endswith(suffix.lower()) and len(lower) > len(suffix):
            return lang

    if ext:
        extensions = langs.get("extensions", {})
        if ext in extensions:
            return extensions[ext]
        if ext.lower() in extensions:
            return extensions[ext.lower()]
        return OTHER

    return _shebang_language(path, langs.get("shebangs", {})) or OTHER


def is_ignored(path: str, globs: list[str]) -> bool:
    norm = path.replace("\\", "/")
    parts = [p for p in norm.split("/") if p]
    for pattern in globs:
        if fnmatch.fnmatchcase(norm, pattern):
            return True
        if any(fnmatch.fnmatchcase(part, pattern) for part in parts):
            return True
    return False


def project_name(cwd: str) -> str:
    try:
        start = Path(cwd).expanduser().resolve()
    except (OSError, RuntimeError):
        return basename(cwd) or "unknown"
    for directory in [start, *start.parents]:
        if (directory / ".git").exists():
            return directory.name or "unknown"
    return start.name or "unknown"


# --------------------------------------------------------------------------- #
# Heartbeats
# --------------------------------------------------------------------------- #


def heartbeat_file(home: Path, day: dt.date) -> Path:
    return heartbeats_dir(home) / ("%s.jsonl" % day.isoformat())


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, (line + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def build_heartbeat(payload: dict[str, Any], cfg: dict[str, Any], now: float | None = None) -> dict[str, Any] | None:
    tool = payload.get("tool_name")
    if tool not in TRACKED_TOOLS:
        return None
    if tool == "Read" and not cfg["track_reads"]:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(path, str) or not path:
        return None
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else os.getcwd()
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    if is_ignored(path, cfg["ignore_globs"]):
        return None
    return {
        "v": SCHEMA_VERSION,
        "ts": round(time.time() if now is None else now, 3),
        "lang": detect_language(path, cfg["language_overrides"]),
        "project": project_name(cwd),
        "tool": tool,
        "session": str(payload.get("session_id") or "")[:12],
        "write": tool != "Read",
    }


def iter_heartbeat_files(home: Path):
    directory = heartbeats_dir(home)
    if not directory.is_dir():
        return
    for entry in sorted(directory.iterdir()):
        m = HEARTBEAT_FILE_RE.match(entry.name)
        if not m:
            continue
        try:
            day = dt.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        yield day, entry


def read_heartbeats(home: Path, range_days: int, today: dt.date | None = None) -> list[dict[str, Any]]:
    """Heartbeats of the last `range_days` days, today included (0 = all)."""
    today = today or dt.date.today()
    first_day = None if range_days == 0 else today - dt.timedelta(days=range_days - 1)
    beats = []
    for day, path in iter_heartbeat_files(home):
        if first_day is not None and day < first_day:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                hb = json.loads(line)
            except ValueError:
                continue
            if not isinstance(hb, dict) or not _is_num(hb.get("ts")) or not isinstance(hb.get("lang"), str):
                continue
            beats.append(hb)  # lines without "v" are v0.1.0 heartbeats: same shape
    return beats


def aggregate(
    heartbeats: list[dict[str, Any]],
    timeout_minutes: float,
    exclude: list[str] | None = None,
    key: str = "lang",
) -> dict[str, float]:
    """Seconds per language. All sessions share one timeline, so parallel
    sessions are never counted twice."""
    excluded = set(exclude or [])
    limit = timeout_minutes * 60
    ordered = sorted(heartbeats, key=lambda hb: hb["ts"])
    totals: dict[str, float] = {}
    for current, nxt in zip(ordered, ordered[1:]):
        gap = nxt["ts"] - current["ts"]
        name = current.get(key) or "unknown"
        if 0 < gap <= limit and current.get("lang") not in excluded:
            totals[name] = totals.get(name, 0.0) + gap
    return totals


def summarize(totals: dict[str, float], top_n: int, min_percent: float) -> list[tuple[str, float, float]]:
    """(name, seconds, percent) sorted by time, with small languages, those past
    top_n - 1 and "Other" itself folded into a final "Other" row."""
    total = sum(s for s in totals.values() if s > 0)
    if total <= 0:
        return []
    items = sorted(((n, s) for n, s in totals.items() if s > 0), key=lambda kv: (-kv[1], kv[0]))
    named: list[tuple[str, float]] = []
    other = 0.0
    for name, seconds in items:
        if name != OTHER and seconds / total * 100 >= min_percent and len(named) < top_n - 1:
            named.append((name, seconds))
        else:
            other += seconds
    rows = [(n, s, s / total * 100) for n, s in named]
    if other > 0:
        rows.append((OTHER, other, other / total * 100))
    return rows


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def make_bar(percent: float, bar_length: int, blocks: str) -> str:
    """Text progress bar."""
    markers = len(blocks) - 1
    proportion = percent / 100 * bar_length
    full = int(proportion + 0.5 / markers)
    remainder = int((proportion - full) * markers + 0.5)
    bar = blocks[-1] * full + (blocks[remainder] if remainder > 0 else "")
    return bar.ljust(bar_length, blocks[0])


def format_duration(seconds: float) -> str:
    if seconds < 60:
        secs = int(seconds)
        return "%d sec%s" % (secs, "" if secs == 1 else "s")
    minutes = int(seconds // 60)
    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append("%d hr%s" % (hours, "" if hours == 1 else "s"))
    if minutes or not hours:
        parts.append("%d min%s" % (minutes, "" if minutes == 1 else "s"))
    return " ".join(parts)


def render_rows(rows: list[tuple[str, float, float]], cfg: dict[str, Any], show_time: bool | None = None) -> list[str]:
    show_time = cfg["show_time"] if show_time is None else show_time
    lines = []
    for name, seconds, percent in rows:
        line = name.ljust(cfg["name_width"])
        if show_time:
            line += format_duration(seconds).ljust(16)
        line += make_bar(percent, cfg["bar_length"], cfg["blocks"]) + "   " + "%05.2f %%" % percent
        lines.append(line)
    return lines


def date_range(range_days: int, heartbeats: list[dict[str, Any]], today: dt.date) -> tuple[dt.date, dt.date]:
    if range_days == 0:
        start = dt.date.fromtimestamp(min(hb["ts"] for hb in heartbeats)) if heartbeats else today
    else:
        start = today - dt.timedelta(days=range_days - 1)
    return start, today


def render_block(home: Path, cfg: dict[str, Any], today: dt.date | None = None) -> str | None:
    """The text that goes inside ```txt for the README, or None without data."""
    today = today or dt.date.today()
    beats = read_heartbeats(home, cfg["range_days"], today)
    totals = aggregate(beats, cfg["timeout_minutes"], cfg["exclude_languages"])
    rows = summarize(totals, cfg["top_n"], cfg["min_percent"])
    if not rows:
        return None
    lines = []
    if cfg["show_title"]:
        start, end = date_range(cfg["range_days"], beats, today)
        lines.append("From: %s - To: %s" % (_long_date(start), _long_date(end)))
        if cfg["show_time"]:
            lines.append("Total Time: %s" % format_duration(sum(totals.values())))
        lines.append("")
    lines.extend(render_rows(rows, cfg))
    return "\n".join(lines)


_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def _long_date(day: dt.date) -> str:
    return "%02d %s %d" % (day.day, _MONTHS[day.month - 1], day.year)


def markers(section: str) -> tuple[str, str]:
    return "<!--START_SECTION:%s-->" % section, "<!--END_SECTION:%s-->" % section


def replace_section(text: str, section: str, block: str) -> str:
    start, end = markers(section)
    i = text.find(start)
    j = text.find(end, i + len(start)) if i >= 0 else -1
    if i < 0 or j < 0:
        raise LangstatsError(
            "the README has no %s ... %s markers. Add them where the stats should go, "
            "or run /langstats:setup to insert them." % (start, end)
        )
    return text[: i + len(start)] + "\n\n```txt\n" + block + "\n```\n\n" + text[j:]


def markers_snippet(section: str) -> str:
    start, end = markers(section)
    return "%s\n%s\n" % (start, end)


def snippet_text(section: str, block: str) -> str:
    """The block with its markers, exactly as `publish` would write it."""
    return replace_section(markers_snippet(section), section, block)


def write_snippet(home: Path, cfg: dict[str, Any], block: str) -> str:
    text = snippet_text(cfg["section"], block)
    home.mkdir(parents=True, exist_ok=True)
    (home / SNIPPET_FILE).write_text(text, encoding="utf-8")
    return text


def copy_to_clipboard(text: str) -> str | None:
    """Copy with the platform's clipboard tool. Returns the tool used, or None."""
    import shutil
    import subprocess

    if sys.platform == "darwin":
        candidates = [["pbcopy"]]
    elif os.name == "nt":
        candidates = [["clip"]]
    else:
        candidates = [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
            ["clip.exe"],
        ]
    for cmd in candidates:
        if shutil.which(cmd[0]) is None:
            continue
        data = ("\ufeff" + text).encode("utf-16-le") if cmd[0].startswith("clip") else text.encode("utf-8")
        try:
            subprocess.run(cmd, input=data, check=True, timeout=5, capture_output=True)
            return cmd[0]
        except (OSError, subprocess.SubprocessError):
            continue
    return None


# --------------------------------------------------------------------------- #
# Publishing
# --------------------------------------------------------------------------- #


def run(cmd: list[str], cwd: Path | None = None, input_text: str | None = None, check: bool = True):
    import subprocess

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        raise LangstatsError("%r is not installed or not on PATH" % cmd[0]) from None
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise LangstatsError("`%s` failed: %s" % (" ".join(cmd), detail))
    return proc


def _git_repo(cfg: dict[str, Any]) -> Path:
    if not cfg["readme_repo_path"]:
        raise LangstatsError("readme_repo_path is not set (mode git). " + SETUP_HINT)
    repo = Path(cfg["readme_repo_path"]).expanduser()
    if not (repo / ".git").exists():
        raise LangstatsError("%s is not a git clone. %s" % (repo, SETUP_HINT))
    return repo


def gh_login() -> str | None:
    """The login of the account `gh` is connected to, or None (gh missing or
    not logged in). Only called when publishing, never from a hook."""
    import shutil

    if shutil.which("gh") is None:
        return None
    try:
        proc = run(["gh", "api", "user", "--jq", ".login"], check=False)
    except LangstatsError:
        return None
    login = proc.stdout.strip()
    return login if proc.returncode == 0 and re.fullmatch(r"[\w-]+", login) else None


NO_GITHUB_HINT = (
    "To publish automatically, install the GitHub CLI (https://cli.github.com) and run `gh auth login`, "
    "then /langstats:setup. Meanwhile, /langstats:snippet gives you the block to paste by hand."
)


def resolve_target(cfg: dict[str, Any]) -> tuple[str, Any]:
    """Decide how to publish: ("git", Path), ("gh", "owner/repo") or ("manual", None).

    mode auto: a configured clone or repo wins; otherwise, when gh is logged in,
    the user's profile README repository <login>/<login>; otherwise manual."""
    mode = cfg["mode"]
    if mode == "manual":
        return "manual", None
    if mode == "git":
        return "git", _git_repo(cfg)
    if mode == "auto" and cfg["readme_repo_path"]:
        return "git", _git_repo(cfg)
    if cfg["readme_repo"]:
        return "gh", cfg["readme_repo"]
    login = gh_login()
    if login:
        return "gh", "%s/%s" % (login, login)
    if mode == "gh":
        raise LangstatsError("gh is not installed or not logged in, and readme_repo is not set. " + NO_GITHUB_HINT)
    return "manual", None


def _has_upstream(repo: Path) -> bool:
    proc = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=repo, check=False)
    return proc.returncode == 0


def _gh_get(repo: str, path: str) -> tuple[str, str]:
    import base64

    proc = run(["gh", "api", "repos/%s/contents/%s" % (repo, path)], check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        if "Not Found" in detail or "404" in detail:
            raise LangstatsError(
                "%s/%s was not found. For a profile README, create the public repository %s "
                "with a README.md (https://github.com/new), or set readme_repo." % (repo, path, repo)
            )
        raise LangstatsError("could not read %s/%s from GitHub: %s" % (repo, path, detail))
    data = json.loads(proc.stdout)
    content = base64.b64decode(data.get("content", "")).decode("utf-8")
    return content, data["sha"]


def _gh_put(repo: str, path: str, text: str, sha: str, message: str) -> None:
    import base64

    body = json.dumps(
        {"message": message, "content": base64.b64encode(text.encode("utf-8")).decode("ascii"), "sha": sha}
    )
    run(["gh", "api", "-X", "PUT", "repos/%s/contents/%s" % (repo, path), "--input", "-"], input_text=body)


def publish(home: Path, cfg: dict[str, Any], dry_run: bool = False, out=None) -> str:
    """Returns "dry-run", "no-data", "manual", "unchanged" or "published"."""
    out = out or sys.stdout
    mode, target = resolve_target(cfg)

    block = render_block(home, cfg)
    if block is None:
        out.write("langstats: no activity in the configured range; nothing to publish.\n")
        return "no-data"

    if dry_run:
        where = {"git": "local clone %s" % target, "gh": "github.com/%s" % target, "manual": "manual (copy and paste)"}
        out.write("langstats: dry run, target: %s/%s\n" % (where[mode], "" if mode == "manual" else cfg["readme_file"]))
        out.write("```txt\n%s\n```\n" % block)
        return "dry-run"

    if mode == "manual":
        snippet = write_snippet(home, cfg, block)
        out.write(
            "langstats: GitHub is not connected, so nothing was published.\n"
            "Paste this into the README.md of your profile repository (github.com/<you>/<you>), "
            "replacing any previous langstats block:\n\n%s\n"
            "Saved to %s\n%s\n" % (snippet, home / SNIPPET_FILE, NO_GITHUB_HINT)
        )
        return "manual"

    if mode == "git":
        repo = target
        if _has_upstream(repo):
            run(["git", "pull", "--ff-only", "--quiet"], cwd=repo)
        readme = repo / cfg["readme_file"]
        if not readme.exists():
            raise LangstatsError("%s does not exist." % readme)
        with open(str(readme), encoding="utf-8", newline="") as fh:
            text = fh.read()
        new = replace_section(text, cfg["section"], block)
        if new == text:
            out.write("langstats: README already up to date.\n")
            return "unchanged"
        with open(str(readme), "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        run(["git", "add", "--", cfg["readme_file"]], cwd=repo)
        run(["git", "commit", "--quiet", "-m", cfg["commit_message"], "--", cfg["readme_file"]], cwd=repo)
        if _has_upstream(repo):
            run(["git", "push", "--quiet"], cwd=repo)
            out.write("langstats: README updated and pushed.\n")
        else:
            out.write("langstats: README updated and committed (no upstream to push to).\n")
    else:
        gh_repo = target
        text, sha = _gh_get(gh_repo, cfg["readme_file"])
        new = replace_section(text, cfg["section"], block)
        if new == text:
            out.write("langstats: README already up to date.\n")
            return "unchanged"
        _gh_put(gh_repo, cfg["readme_file"], new, sha, cfg["commit_message"])
        out.write("langstats: README updated on %s.\n" % gh_repo)
    return "published"


def should_auto_publish(cfg: dict[str, Any], state: dict[str, Any], now: float) -> bool:
    if not cfg["auto_publish"]:
        return False
    if cfg["mode"] == "manual":
        return False
    if cfg["mode"] == "git" and not cfg["readme_repo_path"]:
        return False
    last = max(float(state.get("last_publish") or 0), float(state.get("last_attempt") or 0))
    return now - last >= cfg["publish_interval_hours"] * 3600


def spawn_detached(args: list[str], log_path: Path) -> None:
    """Start `args` in the background, detached from the hook's process group,
    with output appended to `log_path`. Returns immediately."""
    import subprocess

    log_path.parent.mkdir(parents=True, exist_ok=True)
    kwargs: dict[str, Any] = {"stdin": subprocess.DEVNULL, "stderr": subprocess.STDOUT, "close_fds": True}
    if os.name == "nt":
        # start_new_session does not exist on Windows
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0x8) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200
        )
    else:
        kwargs["start_new_session"] = True
    with open(str(log_path), "ab") as log:
        subprocess.Popen(args, stdout=log, **kwargs)


def cleanup_retention(home: Path, retention_days: int, today: dt.date | None = None) -> int:
    if retention_days <= 0:
        return 0
    today = today or dt.date.today()
    cutoff = today - dt.timedelta(days=retention_days)
    removed = 0
    for day, path in list(iter_heartbeat_files(home)):
        if day < cutoff:
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    return removed


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def cmd_hook(args: argparse.Namespace) -> int:
    home = prepare_home()
    buffer = getattr(sys.stdin, "buffer", None)
    raw = buffer.read().decode("utf-8", "replace") if buffer is not None else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    cfg = load_config(home)
    hb = build_heartbeat(payload, cfg)
    if hb is not None:
        append_line(
            heartbeat_file(home, dt.date.fromtimestamp(hb["ts"])),
            json.dumps(hb, ensure_ascii=False, separators=(",", ":")),
        )
    return 0


def cmd_session_start(args: argparse.Namespace) -> int:
    home = prepare_home()
    cfg = load_config(home)
    cleanup_retention(home, cfg["retention_days"])
    return 0


def cmd_session_end(args: argparse.Namespace) -> int:
    home = prepare_home()
    cfg = load_config(home)
    now = time.time()
    if should_auto_publish(cfg, read_state(home), now):
        update_state(home, last_attempt=now)
        spawn_detached([sys.executable, str(SCRIPT_PATH), "publish", "--auto"], home / "publish.log")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    home = prepare_home()
    cfg = load_config(home)
    days = cfg["range_days"] if args.days is None else args.days
    if days < 0:
        raise LangstatsError("--days must be >= 0")
    today = dt.date.today()
    beats = read_heartbeats(home, days, today)
    if args.project:
        beats = [hb for hb in beats if hb.get("project") == args.project]
    totals = aggregate(beats, cfg["timeout_minutes"], cfg["exclude_languages"])
    rows = summarize(totals, cfg["top_n"], cfg["min_percent"])
    start, end = date_range(days, beats, today)
    label = "all time" if days == 0 else "last %d day%s" % (days, "" if days == 1 else "s")
    print("langstats: %s (%s to %s)%s" % (label, start, end, " - project %s" % args.project if args.project else ""))
    if not rows:
        print("No activity recorded yet. Heartbeats are stored in %s" % heartbeats_dir(home))
        return 0
    print("Total: %s across %d heartbeats" % (format_duration(sum(totals.values())), len(beats)))
    print()
    for line in render_rows(rows, cfg, show_time=True):
        print(line)
    if not args.project:
        projects = summarize(aggregate(beats, cfg["timeout_minutes"], cfg["exclude_languages"], key="project"), 6, 0)
        if projects:
            print()
            print("Projects: " + ", ".join("%s %s" % (n, format_duration(s)) for n, s, _ in projects))
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    home = prepare_home()
    cfg = load_config(home)
    if args.auto:
        sys.stdout.write("[%s] auto-publish\n" % dt.datetime.now().isoformat(timespec="seconds"))
    result = publish(home, cfg, dry_run=args.dry_run)
    if result in ("published", "unchanged"):  # no-data / manual / dry-run do not count
        update_state(home, last_publish=time.time())
    return 0


def cmd_snippet(args: argparse.Namespace) -> int:
    home = prepare_home()
    cfg = load_config(home)
    block = render_block(home, cfg)
    if block is None:
        print("langstats: no activity in the configured range yet; nothing to paste.")
        return 0
    text = write_snippet(home, cfg, block)
    print(text, end="")
    if args.copy:
        tool = copy_to_clipboard(text)
        warn("copied to the clipboard (%s)" % tool if tool else "no clipboard tool found; copy the text above")
    warn("also saved to %s" % (home / SNIPPET_FILE))
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    home = prepare_home()
    if args.action == "path":
        print(config_path(home))
        return 0
    if args.action == "show":
        cfg = load_config(home, report=False)
        try:
            _, problems = validate_config(read_user_config(home))
        except (OSError, ValueError) as exc:
            problems = ["could not read config.json: %s" % exc]
        print("# %s" % config_path(home))
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        for p in problems:
            print("# warning: " + p)
        return 0
    try:
        user = read_user_config(home)
    except (OSError, ValueError) as exc:
        raise LangstatsError("cannot update %s: %s" % (config_path(home), exc)) from None
    if args.action == "set":
        if args.key is None or args.value is None:
            raise LangstatsError("usage: config set <key> <value>")
        user[args.key] = parse_config_value(args.key, args.value)
        write_user_config(home, user)
        print("%s = %s" % (args.key, json.dumps(user[args.key], ensure_ascii=False)))
    elif args.action == "unset":
        if args.key is None:
            raise LangstatsError("usage: config unset <key>")
        user.pop(args.key, None)
        write_user_config(home, user)
        print("%s reset to default (%s)" % (args.key, json.dumps(DEFAULTS.get(args.key), ensure_ascii=False)))
    return 0


def _check(ok: bool, label: str, detail: str = "") -> bool:
    print("[%s] %s%s" % ("ok" if ok else "!!", label, (": " + detail) if detail else ""))
    return ok


def cmd_doctor(args: argparse.Namespace) -> int:
    home = prepare_home()
    good = True
    good &= _check(True, "python", "%d.%d.%d" % sys.version_info[:3])
    try:
        _, problems = validate_config(read_user_config(home))
    except (OSError, ValueError) as exc:
        problems = [str(exc)]
    good &= _check(not problems, "config", "; ".join(problems) or str(config_path(home)))
    cfg = load_config(home, report=False)
    count = sum(1 for _ in iter_heartbeat_files(home))
    _check(True, "heartbeats", "%d day file(s) in %s" % (count, heartbeats_dir(home)))

    try:
        mode, target = resolve_target(cfg)
    except LangstatsError as exc:
        _check(False, "target (mode %s)" % cfg["mode"], str(exc))
        print("not ready: fix the items marked [!!]")
        return 1

    text = None
    if mode == "manual":
        _check(
            True,
            "target (mode %s)" % cfg["mode"],
            "manual: GitHub is not connected; /langstats:snippet prints the block to paste. " + NO_GITHUB_HINT,
        )
    elif mode == "git":
        good &= _check(True, "target (mode %s)" % cfg["mode"], "local clone %s" % target)
        readme = target / cfg["readme_file"]
        if _check(readme.exists(), "README file", str(readme)):
            text = readme.read_text(encoding="utf-8")
        else:
            good = False
    else:
        good &= _check(True, "target (mode %s)" % cfg["mode"], "github.com/%s via gh" % target)
        try:
            text, _ = _gh_get(target, cfg["readme_file"])
            _check(True, "README file", "%s/%s" % (target, cfg["readme_file"]))
        except LangstatsError as exc:
            good &= _check(False, "README file", str(exc))

    if text is not None:
        start, end = markers(cfg["section"])
        i = text.find(start)
        has = i >= 0 and text.find(end, i + len(start)) >= 0
        good &= _check(
            has, "section markers", "%s ... %s" % (start, end) + ("" if has else " not found (run insert-markers)")
        )
    print("ready to publish (%s)" % mode if good else "not ready: fix the items marked [!!]")
    return 0 if good else 1


def _append_markers(text: str, snippet: str) -> str:
    sep = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    return text + sep + snippet


def cmd_insert_markers(args: argparse.Namespace) -> int:
    home = prepare_home()
    cfg = load_config(home)
    start, end = markers(cfg["section"])
    snippet = markers_snippet(cfg["section"])
    mode, target = resolve_target(cfg)
    if mode == "manual":
        print("langstats: GitHub is not connected. Add these two lines to your README where the stats should go:")
        print()
        print(snippet)
        return 0
    if mode == "git":
        readme = target / cfg["readme_file"]
        text = readme.read_text(encoding="utf-8") if readme.exists() else ""
        if start in text and end in text:
            print("langstats: markers already present in %s" % readme)
            return 0
        with open(str(readme), "w", encoding="utf-8", newline="") as fh:
            fh.write(_append_markers(text, snippet))
        print("langstats: markers added at the end of %s (committed with the next publish)" % readme)
    else:
        text, sha = _gh_get(target, cfg["readme_file"])
        if start in text and end in text:
            print("langstats: markers already present in %s/%s" % (target, cfg["readme_file"]))
            return 0
        message = "chore(readme): add langstats section markers"
        _gh_put(target, cfg["readme_file"], _append_markers(text, snippet), sha, message)
        print("langstats: markers added at the end of %s/%s" % (target, cfg["readme_file"]))
    return 0


# Hooks bypass argparse entirely: they run after every Read/Edit.
HOOK_HANDLERS = {
    "hook": lambda: cmd_hook(None),
    "session-start": lambda: cmd_session_start(None),
    "session-end": lambda: cmd_session_end(None),
}
HOOK_COMMANDS = set(HOOK_HANDLERS)


def build_parser() -> argparse.ArgumentParser:
    import argparse

    parser = argparse.ArgumentParser(prog="langstats", description="Language stats for Claude Code sessions.")
    parser.add_argument("--version", action="version", version="langstats " + __version__)
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="report errors on stderr but exit with code 0 (used by the slash commands)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("hook", help="PostToolUse hook (payload on stdin)").set_defaults(func=cmd_hook)
    sub.add_parser("session-start", help="SessionStart hook").set_defaults(func=cmd_session_start)
    sub.add_parser("session-end", help="SessionEnd hook").set_defaults(func=cmd_session_end)

    p = sub.add_parser("stats", help="print the language table")
    p.add_argument("--days", type=int, default=None, help="range in days (0 = all); default: range_days")
    p.add_argument("--project", default=None, help="only this project")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("publish", help="update the README section, or print it to paste by hand")
    p.add_argument("--dry-run", action="store_true", help="print the block without changing anything")
    p.add_argument("--auto", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("snippet", help="print the README block with its markers, ready to paste")
    p.add_argument("--copy", action="store_true", help="also copy it to the clipboard")
    p.set_defaults(func=cmd_snippet)

    p = sub.add_parser("config", help="show or change the configuration")
    p.add_argument("action", choices=["show", "set", "unset", "path"])
    p.add_argument("key", nargs="?")
    p.add_argument("value", nargs="?")
    p.set_defaults(func=cmd_config)

    sub.add_parser("doctor", help="check the setup").set_defaults(func=cmd_doctor)
    sub.add_parser("insert-markers", help="append the section markers to the README").set_defaults(
        func=cmd_insert_markers
    )
    return parser


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 1 and argv[0] in HOOK_HANDLERS:
        try:
            return HOOK_HANDLERS[argv[0]]()
        except Exception as exc:  # noqa: BLE001 - hooks must never break the session
            warn("hook error: %s: %s" % (type(exc).__name__, exc))
            return 0

    _utf8_stdio()
    soft = "--exit-zero" in argv
    try:
        args = build_parser().parse_args(argv)
        code = args.func(args)
        return 0 if soft else code
    except LangstatsError as exc:
        warn(str(exc))
        return 0 if soft else 1
    except SystemExit as exc:
        if soft and exc.code not in (0, None):
            return 0
        raise


if __name__ == "__main__":
    sys.exit(main())
