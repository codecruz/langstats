"""The PostToolUse hook runs after every Read/Edit: keep it light."""

import json
import os
import subprocess
import sys
import time

import pytest

from conftest import ROOT

SCRIPT = ROOT / "scripts" / "langstats.py"
PAYLOAD = json.dumps({"session_id": "s", "cwd": "/w", "tool_name": "Edit", "tool_input": {"file_path": "/w/a.py"}})
HEAVY = ["argparse", "subprocess", "shutil", "base64"]


def test_hook_path_does_not_import_heavy_modules(tmp_path):
    code = (
        "import io, sys, json; sys.path.insert(0, %r); "
        "sys.stdin = io.TextIOWrapper(io.BytesIO(%r.encode())); "
        "import langstats; langstats.main(['hook']); "
        "print(json.dumps([m for m in %r if m in sys.modules]))"
    ) % (str(SCRIPT.parent), PAYLOAD, HEAVY)
    env = dict(os.environ, LANGSTATS_HOME=str(tmp_path / "h"), LANGTIME_HOME=str(tmp_path / "none"))
    proc = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env, check=True)
    assert json.loads(proc.stdout.strip().splitlines()[-1]) == []
    assert list((tmp_path / "h" / "heartbeats").glob("*.jsonl"))


def test_hook_overhead_is_small(tmp_path):
    """Our work on top of the interpreter's own startup stays small."""
    env = dict(os.environ, LANGSTATS_HOME=str(tmp_path / "h"), LANGTIME_HOME=str(tmp_path / "none"))

    def best(cmd, stdin=""):
        times = []
        for _ in range(5):
            t0 = time.perf_counter()
            subprocess.run(cmd, input=stdin, capture_output=True, text=True, env=env, check=True)
            times.append(time.perf_counter() - t0)
        return min(times)

    baseline = best([sys.executable, "-I", "-c", "pass"])
    hook = best([sys.executable, "-I", str(SCRIPT), "hook"], PAYLOAD)
    assert hook - baseline < 0.1, "hook overhead %.0f ms" % ((hook - baseline) * 1000)


@pytest.mark.skipif(os.name == "nt", reason="sh launcher; Windows uses run.cmd in CI")
def test_launcher_caches_interpreter(tmp_path):
    home = tmp_path / "h"
    env = dict(os.environ, LANGSTATS_HOME=str(home), LANGTIME_HOME=str(tmp_path / "none"))
    env.pop("LANGSTATS_PYTHON", None)
    run = ["sh", str(ROOT / "scripts" / "run"), "--version"]
    out = subprocess.run(run, capture_output=True, text=True, env=env, check=True).stdout
    assert "langstats" in out
    cache = home / ".python"
    assert cache.read_text().strip() in ("python3", "python", "py -3")
    # a stale cache falls back to discovery and is rewritten
    cache.write_text("no-such-python-xyz\n")
    out = subprocess.run(run, capture_output=True, text=True, env=env, check=True).stdout
    assert "langstats" in out and cache.read_text().strip() != "no-such-python-xyz"
