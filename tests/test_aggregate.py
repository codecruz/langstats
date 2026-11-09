"""A4 / A5: time aggregation, plus top-N / Other grouping."""

import langstats


def hb(ts, lang, session="s1", project="p"):
    return {"ts": float(ts), "lang": lang, "session": session, "project": project}


def test_simple_gaps_go_to_first_language():
    beats = [hb(0, "Python"), hb(60, "Go"), hb(180, "Python")]
    assert langstats.aggregate(beats, 15) == {"Python": 60.0, "Go": 120.0}


def test_order_independent():
    beats = [hb(180, "Python"), hb(0, "Python"), hb(60, "Go")]
    assert langstats.aggregate(beats, 15) == {"Python": 60.0, "Go": 120.0}


def test_a4_interleaved_sessions_never_exceed_wall_clock():
    a = [hb(t, "Python", "A") for t in range(0, 3600, 120)]
    b = [hb(t + 60, "Go", "B") for t in range(0, 3600, 120)]
    beats = a + b
    totals = langstats.aggregate(beats, 15)
    wall = max(x["ts"] for x in beats) - min(x["ts"] for x in beats)
    assert sum(totals.values()) <= wall
    assert sum(totals.values()) == wall  # continuous activity: exactly the wall clock


def test_a4_simultaneous_heartbeats_count_once():
    beats = [hb(0, "Python", "A"), hb(0, "Go", "B"), hb(100, "Python", "A"), hb(100, "Go", "B")]
    assert sum(langstats.aggregate(beats, 15).values()) == 100


def test_a5_gaps_over_timeout_are_not_counted():
    beats = [hb(0, "Python"), hb(15 * 60, "Python"), hb(15 * 60 + 15 * 60 + 1, "Go"), hb(10_000, "Go")]
    assert langstats.aggregate(beats, 15) == {"Python": 900.0}


def test_a5_custom_timeout():
    beats = [hb(0, "Python"), hb(120, "Python")]
    assert langstats.aggregate(beats, 1) == {}
    assert langstats.aggregate(beats, 2) == {"Python": 120.0}


def test_exclude_languages():
    beats = [hb(0, "Markdown"), hb(60, "Python"), hb(120, "Python")]
    assert langstats.aggregate(beats, 15, ["Markdown"]) == {"Python": 60.0}


def test_summarize_groups_into_other():
    totals = {"A": 50, "B": 20, "C": 10, "D": 9, "E": 6, "F": 4.6, "Other": 0.4}
    rows = langstats.summarize(totals, top_n=4, min_percent=0.5)
    assert [r[0] for r in rows] == ["A", "B", "C", "Other"]
    assert abs(rows[-1][2] - 20.0) < 1e-9
    assert abs(sum(r[2] for r in rows) - 100) < 1e-9


def test_summarize_min_percent():
    rows = langstats.summarize({"A": 99.6, "B": 0.4}, top_n=7, min_percent=0.5)
    assert [r[0] for r in rows] == ["A", "Other"]


def test_summarize_no_other_row_when_empty():
    rows = langstats.summarize({"A": 3, "B": 1}, top_n=7, min_percent=0.5)
    assert [(r[0], r[2]) for r in rows] == [("A", 75.0), ("B", 25.0)]


def test_summarize_empty():
    assert langstats.summarize({}, 7, 0.5) == []


def test_non_code_and_other_left_out_by_default():
    cfg = dict(langstats.DEFAULTS)
    excluded = langstats.excluded_languages(cfg)
    assert {"Markdown", "JSON", "YAML", "Other"} <= excluded
    assert not {"Python", "JavaScript", "HTML", "CSS", "Shell", "SQL"} & excluded


def test_count_non_code_keeps_only_user_exclusions():
    cfg = dict(langstats.DEFAULTS, count_non_code=True, exclude_languages=["Go"])
    assert langstats.excluded_languages(cfg) == {"Go"}
