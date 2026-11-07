"""A1: the progress bar renders exactly; row and section format."""

import pytest

import langstats

EMOJI = "·🚀💮"  # empty, half, full (the v0.1.0 block)


def ref_bar(full, half, length=25):
    return "💮" * full + "🚀" * half + "·" * (length - full - half)


@pytest.mark.parametrize(
    "percent, full, half",
    [
        (24.10, 6, 0),
        (20.04, 5, 0),
        (17.90, 4, 1),
        (12.18, 3, 0),
        (7.45, 2, 0),
        (5.16, 1, 1),
        (3.46, 1, 0),
    ],
)
def test_a1_reference_bars(percent, full, half):
    assert langstats.make_bar(percent, 25, EMOJI) == ref_bar(full, half)


@pytest.mark.parametrize("percent", [0, 0.01, 33.3, 50, 99.99, 100])
def test_bar_always_has_bar_length(percent):
    for blocks in (EMOJI, "░▒▓█", "-#"):
        assert len(langstats.make_bar(percent, 25, blocks)) == 25


def test_bar_extremes():
    assert langstats.make_bar(0, 10, "░▒▓█") == "░" * 10
    assert langstats.make_bar(100, 10, "░▒▓█") == "█" * 10


def test_row_format():
    cfg = dict(langstats.DEFAULTS, blocks=EMOJI)
    [line] = langstats.render_rows([("PHP", 100.0, 7.45)], cfg)
    assert line == "PHP".ljust(32) + ref_bar(2, 0) + "   07.45 %"


def test_row_format_with_time():
    cfg = dict(langstats.DEFAULTS, show_time=True)
    [line] = langstats.render_rows([("Go", 3 * 3600 + 5 * 60, 50.0)], cfg)
    assert line.startswith("Go".ljust(32) + "3 hrs 5 mins".ljust(16))
    assert line.endswith("   50.00 %")


@pytest.mark.parametrize(
    "seconds, text",
    [(0, "0 secs"), (1, "1 sec"), (59.9, "59 secs"), (60, "1 min"), (3600, "1 hr"), (7260, "2 hrs 1 min")],
)
def test_format_duration(seconds, text):
    assert langstats.format_duration(seconds) == text


def test_replace_section_format():
    text = "# Hi\n\n<!--START_SECTION:langstats-->\nold stuff\n<!--END_SECTION:langstats-->\n\nbye\n"
    new = langstats.replace_section(text, "langstats", "A\nB")
    assert new == ("# Hi\n\n<!--START_SECTION:langstats-->\n\n```txt\nA\nB\n```\n\n<!--END_SECTION:langstats-->\n\nbye\n")
    # idempotent
    assert langstats.replace_section(new, "langstats", "A\nB") == new


def test_replace_section_only_named_section():
    text = "<!--START_SECTION:a-->x<!--END_SECTION:a-->\n<!--START_SECTION:b-->y<!--END_SECTION:b-->"
    new = langstats.replace_section(text, "b", "Z")
    assert new.startswith("<!--START_SECTION:a-->x<!--END_SECTION:a-->\n")
    assert "Z" in new


@pytest.mark.parametrize(
    "text",
    ["no markers", "<!--START_SECTION:langstats--> only start", "<!--END_SECTION:langstats--><!--START_SECTION:langstats-->"],
)
def test_replace_section_missing_markers(text):
    with pytest.raises(langstats.LangstatsError, match="START_SECTION:langstats"):
        langstats.replace_section(text, "langstats", "x")
