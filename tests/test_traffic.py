"""tools/traffic.py: merges GitHub's 14-day traffic into a growing CSV."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_traffic():
    spec = importlib.util.spec_from_file_location("traffic", ROOT / "tools" / "traffic.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def day(date, count, uniques):
    return {"timestamp": date + "T00:00:00Z", "count": count, "uniques": uniques}


def test_merge_keeps_history_and_updates_days(tmp_path):
    traffic = load_traffic()
    path = tmp_path / "traffic.csv"
    first = traffic.merge(
        {},
        {"clones": [day("2026-01-01", 5, 2), day("2026-01-02", 1, 1)]},
        {"views": [day("2026-01-01", 9, 4)]},
    )
    traffic.write_csv(path, first)
    # 14 days later the API no longer returns 2026-01-01, and has more for 2026-01-02
    second = traffic.merge(traffic.read_csv(path), {"clones": [day("2026-01-02", 3, 2)]}, {"views": []})
    traffic.write_csv(path, second)
    assert path.read_text(encoding="utf-8") == (
        "date,clones,unique_cloners,views,unique_visitors\n2026-01-01,5,2,9,4\n2026-01-02,3,2,0,0\n"
    )


def test_main_needs_a_token(monkeypatch, tmp_path, capsys):
    traffic = load_traffic()
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert traffic.main(["owner/repo", str(tmp_path / "t.csv")]) == 1
    assert "GH_TOKEN" in capsys.readouterr().err
    assert not (tmp_path / "t.csv").exists()
