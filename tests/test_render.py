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


# --- configurable bar styles ------------------------------------------------


@pytest.mark.parametrize("name", list(langstats.BAR_STYLES))
def test_every_style_renders_full_length(name):
    symbols = langstats.BAR_STYLES[name]
    for percent in (0, 3.46, 17.9, 50, 99.9, 100):
        bar = langstats.make_bar(percent, 25, name)
        assert bar.count(symbols[0]) + sum(bar.count(s) for s in symbols[1:]) == 25


def test_style_name_string_and_list_are_equivalent():
    as_name = langstats.make_bar(17.9, 25, "rocket")
    assert as_name == langstats.make_bar(17.9, 25, "·🚀💮") == langstats.make_bar(17.9, 25, ["·", "🚀", "💮"])
    assert as_name == ref_bar(4, 1)


def test_multi_codepoint_emoji_symbols():
    bar = langstats.make_bar(17.9, 25, ["·", "❤️", "💖"])
    assert bar == "💖" * 4 + "❤️" + "·" * 20


def test_two_symbol_style_has_no_partial():
    assert langstats.make_bar(17.9, 10, "☆★") == "★★☆☆☆☆☆☆☆☆"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("flowers", "flowers"),
        ("·🌱🌸", "·🌱🌸"),
        ("· ❤️ 💖", ["·", "❤️", "💖"]),
        ('["-", "#"]', ["-", "#"]),
    ],
)
def test_parse_blocks(raw, expected):
    assert langstats.parse_config_value("blocks", raw) == expected


@pytest.mark.parametrize("raw", ["x", "[]", '["only"]', '["a", ""]'])
def test_parse_blocks_rejects(raw):
    with pytest.raises(langstats.LangstatsError):
        langstats.parse_config_value("blocks", raw)


def test_style_command_lists_and_sets(home, capsys):
    assert langstats.main(["style"]) == 0
    out = capsys.readouterr().out
    assert "flowers" in out and "🌸" in out and "Current style" in out
    assert langstats.main(["style", "flowers"]) == 0
    assert langstats.load_config(home)["blocks"] == "flowers"
    assert "🌸" in capsys.readouterr().out
    assert langstats.main(["style", "·", "❤️", "💖"]) == 0
    assert langstats.load_config(home)["blocks"] == ["·", "❤️", "💖"]


def test_style_command_rejects_invalid(home, capsys):
    assert langstats.main(["style", "x"]) == 1
    assert "flowers" in capsys.readouterr().err
