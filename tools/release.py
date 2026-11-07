#!/usr/bin/env python3
"""Prepare a release: bump the version everywhere and close the changelog.

    python3 tools/release.py 0.5.0

Claude Code only updates the plugin when its version changes, so this bumps it in
every file that holds it, moves *Unreleased* in CHANGELOG.md to the new version
and updates the compare links. Commit and push the result to main; once CI
passes, the release workflow creates the tag and the GitHub release.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
REPO_URL = "https://github.com/codecruz/langstats"


class ReleaseError(Exception):
    pass


def parse(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def current_version(root: Path) -> str:
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return plugin["version"]


def replace_once(path: Path, old: str, new: str) -> str:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise ReleaseError("%s: expected exactly one %r" % (path.name, old))
    return text.replace(old, new)


def close_changelog(path: Path, old: str, new: str, date: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[)", text, flags=re.S | re.M)
    if not match:
        raise ReleaseError("CHANGELOG.md: no '## [Unreleased]' section followed by a version")
    if not match.group(1).strip():
        raise ReleaseError("CHANGELOG.md: the Unreleased section is empty; describe the changes first")
    text = text.replace("## [Unreleased]\n", "## [Unreleased]\n\n## [%s] - %s\n" % (new, date), 1)
    old_link = "[Unreleased]: %s/compare/v%s...HEAD\n" % (REPO_URL, old)
    if text.count(old_link) != 1:
        raise ReleaseError("CHANGELOG.md: expected the link %r" % old_link.strip())
    new_links = "[Unreleased]: %s/compare/v%s...HEAD\n[%s]: %s/compare/v%s...v%s\n" % (
        REPO_URL,
        new,
        new,
        REPO_URL,
        old,
        new,
    )
    text = text.replace(old_link, new_links)
    return re.sub(r"\n{3,}(?=## \[)", "\n\n", text)


def release(root: Path, new: str, date: str) -> str:
    if not VERSION_RE.match(new):
        raise ReleaseError("the version must look like 1.2.3, got %r" % new)
    old = current_version(root)
    if parse(new) <= parse(old):
        raise ReleaseError("the new version %s must be greater than the current one, %s" % (new, old))
    # Compute every change first, so a failure leaves no file half updated.
    changes = {root / "CHANGELOG.md": close_changelog(root / "CHANGELOG.md", old, new, date)}
    for name in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        changes[root / name] = replace_once(root / name, '"version": "%s"' % old, '"version": "%s"' % new)
    changes[root / "pyproject.toml"] = replace_once(
        root / "pyproject.toml", 'version = "%s"' % old, 'version = "%s"' % new
    )
    changes[root / "scripts" / "langstats.py"] = replace_once(
        root / "scripts" / "langstats.py", '__version__ = "%s"' % old, '__version__ = "%s"' % new
    )
    for path, text in changes.items():
        with open(path, "w", encoding="utf-8", newline="") as f:  # write_text(newline=) needs 3.10
            f.write(text)
    return old


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bump the version and close the changelog for a release.")
    parser.add_argument("version", help="new version, for example 0.5.0")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="release date (default: today)")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        old = release(args.root, args.version, args.date)
    except (ReleaseError, OSError, KeyError, ValueError) as exc:
        print("release: %s" % exc, file=sys.stderr)
        return 1
    print("Version %s -> %s. Next:" % (old, args.version))
    print('  git commit -am "release: %s" && git push' % args.version)
    print("CI runs, and when it passes the release workflow tags v%s and publishes the release." % args.version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
