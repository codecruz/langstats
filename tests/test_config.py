"""Config loading, validation, config set/show, migration (A11), retention."""

import datetime as dt
import json

import pytest

import langstats
from conftest import heartbeat_lines


def test_defaults_have_no_personal_values():
    assert langstats.DEFAULTS["readme_repo_path"] is None
    assert langstats.DEFAULTS["readme_repo"] is None
    assert langstats.DEFAULTS["mode"] == "auto"


def test_missing_config_gives_defaults(home):
    assert langstats.load_config(home) == langstats.DEFAULTS


def test_user_values_merge_over_defaults(home, write_config):
    write_config(top_n=3, section="langstats")
    cfg = langstats.load_config(home)
    assert cfg["top_n"] == 3 and cfg["section"] == "langstats" and cfg["range_days"] == 7


@pytest.mark.parametrize(
    "key, value",
    [
        ("mode", "svn"),
        ("top_n", 0),
        ("top_n", "7"),
        ("top_n", True),
        ("min_percent", 101),
        ("blocks", "x"),
        ("timeout_minutes", 0),
        ("readme_repo", "not a repo"),
        ("exclude_languages", "Python"),
        ("language_overrides", {".x": 1}),
        ("section", "has space"),
    ],
)
def test_invalid_values_fall_back_with_warning(home, write_config, capsys, key, value):
    write_config(**{key: value})
    cfg = langstats.load_config(home)
    assert cfg[key] == langstats.DEFAULTS[key]
    assert key in capsys.readouterr().err


def test_unknown_key_warns(home, write_config, capsys):
    write_config(colour="blue")
    langstats.load_config(home)
    assert "unknown config key" in capsys.readouterr().err


@pytest.mark.parametrize(
    "key, raw, expected",
    [
        ("mode", "gh", "gh"),
        ("mode", "manual", "manual"),
        ("readme_repo", "me/me", "me/me"),
        ("readme_repo", "null", None),
        ("readme_repo_path", "~/code/me", "~/code/me"),
        ("top_n", "5", 5),
        ("min_percent", "1.5", 1.5),
        ("timeout_minutes", "20", 20),
        ("auto_publish", "yes", True),
        ("show_time", "false", False),
        ("exclude_languages", "Markdown, JSON", ["Markdown", "JSON"]),
        ("exclude_languages", '["Text"]', ["Text"]),
        ("language_overrides", '{".tpl": "Smarty"}', {".tpl": "Smarty"}),
    ],
)
def test_parse_config_value(key, raw, expected):
    assert langstats.parse_config_value(key, raw) == expected


@pytest.mark.parametrize("key, raw", [("top_n", "abc"), ("mode", "svn"), ("auto_publish", "maybe"), ("nope", "1")])
def test_parse_config_value_rejects(key, raw):
    with pytest.raises(langstats.LangstatsError):
        langstats.parse_config_value(key, raw)


def test_config_set_show_unset(home, capsys):
    assert langstats.main(["config", "set", "mode", "gh"]) == 0
    assert langstats.main(["config", "set", "readme_repo", "me/me"]) == 0
    assert json.loads((home / "config.json").read_text(encoding="utf-8")) == {"mode": "gh", "readme_repo": "me/me"}
    capsys.readouterr()
    assert langstats.main(["config", "show"]) == 0
    out = capsys.readouterr().out
    assert '"readme_repo": "me/me"' in out
    assert langstats.main(["config", "unset", "mode"]) == 0
    assert json.loads((home / "config.json").read_text(encoding="utf-8")) == {"readme_repo": "me/me"}


def test_config_set_invalid_fails(home, capsys):
    assert langstats.main(["config", "set", "top_n", "-1"]) == 1
    assert "top_n" in capsys.readouterr().err
    assert not (home / "config.json").exists()


# --- A11: migration from langtime ------------------------------------------


def test_a11_migrates_legacy_data_once(tmp_path, monkeypatch, run_hook):
    home = tmp_path / "langstats"
    legacy = tmp_path / "langtime"
    (legacy / "heartbeats").mkdir(parents=True)
    (legacy / "config.json").write_text(json.dumps({"top_n": 4}), encoding="utf-8")
    old = {"ts": 1.0, "lang": "PHP", "project": "x", "tool": "Edit", "session": "s", "write": True}
    (legacy / "heartbeats" / "2026-11-01.jsonl").write_text(json.dumps(old) + "\n", encoding="utf-8")
    monkeypatch.setenv("LANGSTATS_HOME", str(home))
    monkeypatch.setenv("LANGTIME_HOME", str(legacy))

    assert langstats.main(["session-start"]) == 0
    assert langstats.load_config(home)["top_n"] == 4
    assert heartbeat_lines(home)[0]["lang"] == "PHP"
    assert (home / ".migrated-from-langtime").exists()

    # later changes in the legacy dir are not copied again
    (legacy / "config.json").write_text(json.dumps({"top_n": 2}), encoding="utf-8")
    (legacy / "heartbeats" / "2026-11-02.jsonl").write_text(json.dumps(old) + "\n", encoding="utf-8")
    assert langstats.main(["session-start"]) == 0
    assert langstats.load_config(home)["top_n"] == 4
    assert not (home / "heartbeats" / "2026-11-02.jsonl").exists()


def test_a11_no_migration_when_destination_has_data(tmp_path, monkeypatch):
    home = tmp_path / "langstats"
    (home / "heartbeats").mkdir(parents=True)
    legacy = tmp_path / "langtime"
    legacy.mkdir()
    (legacy / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("LANGSTATS_HOME", str(home))
    monkeypatch.setenv("LANGTIME_HOME", str(legacy))
    assert langstats.migrate_legacy(home) is False
    assert not (home / "config.json").exists()


# --- retention --------------------------------------------------------------


def test_retention_deletes_old_files(home):
    d = home / "heartbeats"
    d.mkdir(parents=True)
    today = dt.date(2026, 11, 7)
    for day in ("2025-11-06", "2025-11-07", "2026-11-07"):
        (d / ("%s.jsonl" % day)).write_text("", encoding="utf-8")
    (d / "notes.txt").write_text("", encoding="utf-8")
    assert langstats.cleanup_retention(home, 365, today) == 1
    assert sorted(p.name for p in d.iterdir()) == ["2025-11-07.jsonl", "2026-11-07.jsonl", "notes.txt"]
    assert langstats.cleanup_retention(home, 0, today) == 0


def test_read_heartbeats_range(home):
    d = home / "heartbeats"
    d.mkdir(parents=True)
    today = dt.date(2026, 11, 7)
    for day in ("2026-10-31", "2026-11-01", "2026-11-07"):
        (d / ("%s.jsonl" % day)).write_text(json.dumps({"ts": 1, "lang": day}) + "\nbad line\n", encoding="utf-8")
    langs = lambda n: sorted(hb["lang"] for hb in langstats.read_heartbeats(home, n, today))  # noqa: E731
    assert langs(7) == ["2026-11-01", "2026-11-07"]
    assert langs(1) == ["2026-11-07"]
    assert langs(0) == ["2026-10-31", "2026-11-01", "2026-11-07"]


def test_a11_migrates_into_home_that_only_holds_the_launcher_cache(tmp_path, monkeypatch):
    home = tmp_path / "langstats"
    home.mkdir()
    (home / ".python").write_text("python3\n", encoding="utf-8")
    legacy = tmp_path / "langtime"
    legacy.mkdir()
    (legacy / "config.json").write_text(json.dumps({"top_n": 3}), encoding="utf-8")
    monkeypatch.setenv("LANGSTATS_HOME", str(home))
    monkeypatch.setenv("LANGTIME_HOME", str(legacy))
    assert langstats.migrate_legacy(home) is True
    assert langstats.load_config(home)["top_n"] == 3
