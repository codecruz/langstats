"""A2 / A3: the PostToolUse hook."""

import json
import subprocess
import sys

import pytest

from conftest import ROOT, heartbeat_lines


def payload(tool="Edit", path="/work/app/main.py", **extra):
    data = {
        "session_id": "abc123def456ghi789",
        "cwd": "/work/app",
        "tool_name": tool,
        "tool_input": {"file_path": path},
    }
    data.update(extra)
    return json.dumps(data)


def test_a2_valid_payload_appends_heartbeat(home, run_hook):
    assert run_hook(payload()) == 0
    [hb] = heartbeat_lines(home)
    assert hb["lang"] == "Python"
    assert hb["tool"] == "Edit"
    assert hb["write"] is True
    assert hb["session"] == "abc123def456"
    assert hb["v"] == 1
    assert hb["project"] == "app"
    assert isinstance(hb["ts"], float)
    assert "path" not in hb and "/work" not in json.dumps(hb)  # no file paths stored


def test_a2_read_and_notebook(home, run_hook):
    run_hook(payload(tool="Read", path="/work/app/index.ts"))
    run_hook(
        json.dumps(
            {"session_id": "s", "cwd": "/w", "tool_name": "NotebookEdit", "tool_input": {"notebook_path": "/w/a.ipynb"}}
        )
    )
    a, b = heartbeat_lines(home)
    assert (a["lang"], a["write"]) == ("TypeScript", False)
    assert (b["lang"], b["write"]) == ("Jupyter Notebook", True)


def test_a2_appends(home, run_hook):
    for _ in range(3):
        run_hook(payload())
    assert len(heartbeat_lines(home)) == 3


def test_relative_path_uses_cwd(home, run_hook):
    run_hook(payload(path="node_modules/x.js"))
    assert heartbeat_lines(home) == []


@pytest.mark.parametrize(
    "stdin_text",
    [
        "",
        "not json",
        "[1, 2]",
        payload(tool="Bash"),
        payload(tool="Grep"),
        payload(path="/home/me/.claude/settings.json"),
        payload(path="/work/app/node_modules/lib/index.js"),
        json.dumps({"tool_name": "Edit", "tool_input": {}}),
        json.dumps({"tool_name": "Edit", "tool_input": "oops"}),
    ],
)
def test_a3_ignored_payloads_write_nothing(home, run_hook, stdin_text):
    assert run_hook(stdin_text) == 0
    assert heartbeat_lines(home) == []


def test_track_reads_false(home, run_hook, write_config):
    write_config(track_reads=False)
    run_hook(payload(tool="Read"))
    run_hook(payload(tool="Write"))
    assert [hb["tool"] for hb in heartbeat_lines(home)] == ["Write"]


def test_invalid_config_does_not_break_hook(home, run_hook, capsys):
    home.mkdir(parents=True)
    (home / "config.json").write_text("{broken", encoding="utf-8")
    assert run_hook(payload()) == 0
    assert len(heartbeat_lines(home)) == 1
    assert "using defaults" in capsys.readouterr().err


@pytest.mark.parametrize("stdin_text", ["garbage", payload(tool="Bash"), payload(path="/x/.claude/a.md")])
def test_a3_subprocess_exit_code_zero(home, stdin_text):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "langstats.py"), "hook"],
        input=stdin_text,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert heartbeat_lines(home) == []


def test_hook_unexpected_error_exits_zero(home, run_hook, monkeypatch):
    import langstats

    def boom(*a, **k):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(langstats, "append_line", boom)
    assert run_hook(payload()) == 0


def test_images_and_binaries_are_not_recorded(home, run_hook):
    for path in ("/work/app/screenshot.png", "/work/app/Doc.PDF", "/work/app/font.woff2", "/work/app/app.apk"):
        run_hook(payload(tool="Read", path=path))
    run_hook(payload(tool="Read", path="/work/app/icon.svg"))
    assert [hb["lang"] for hb in heartbeat_lines(home)] == ["SVG"]


def test_override_records_a_skipped_extension(home, run_hook, write_config):
    write_config(language_overrides={".png": "Images"})
    run_hook(payload(tool="Read", path="/work/app/shot.png"))
    assert [hb["lang"] for hb in heartbeat_lines(home)] == ["Images"]
