import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import langstats  # noqa: E402


@pytest.fixture
def home(tmp_path, monkeypatch):
    """An isolated LANGSTATS_HOME, with no legacy langtime directory."""
    h = tmp_path / "langstats-home"
    monkeypatch.setenv("LANGSTATS_HOME", str(h))
    monkeypatch.setenv("LANGTIME_HOME", str(tmp_path / "no-legacy"))
    return h


@pytest.fixture
def run_hook(monkeypatch):
    """Run `langstats hook` in-process with the given stdin text."""

    def _run(stdin_text):
        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
        return langstats.main(["hook"])

    return _run


@pytest.fixture
def write_config(home):
    def _write(**values):
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.json").write_text(json.dumps(values), encoding="utf-8")

    return _write


def heartbeat_lines(home):
    d = home / "heartbeats"
    if not d.exists():
        return []
    lines = []
    for f in sorted(d.glob("*.jsonl")):
        lines += [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
    return lines
