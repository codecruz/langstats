import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import langstats  # noqa: E402


@pytest.fixture(autouse=True)
def no_github(monkeypatch):
    """Tests never talk to the real gh: by default GitHub is not connected."""
    monkeypatch.setattr(langstats, "gh_login", lambda: None)


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


class FakeGitHub:
    """In-memory stand-in for the gh-backed helpers: files[repo][path] = text."""

    def __init__(self):
        self.files = {}
        self.puts = []

    def read(self, repo, path):
        text = self.files.get(repo, {}).get(path)
        return (text, "sha-%d" % hash(text)) if text is not None else (None, None)

    def list(self, repo, directory):
        prefix = directory.rstrip("/") + "/"
        return sorted(
            p[len(prefix) :] for p in self.files.get(repo, {}) if p.startswith(prefix) and "/" not in p[len(prefix) :]
        )

    def put(self, repo, path, text, sha, message):
        current = self.files.setdefault(repo, {}).get(path)
        if sha != (None if current is None else "sha-%d" % hash(current)):
            raise langstats.StoreConflict("409 sha does not match")
        self.files[repo][path] = text
        self.puts.append(path)


@pytest.fixture
def fake_github(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(langstats, "_gh_read", fake.read)
    monkeypatch.setattr(langstats, "_gh_list", fake.list)
    monkeypatch.setattr(langstats, "_gh_put", fake.put)
    return fake
