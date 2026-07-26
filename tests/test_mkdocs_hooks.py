# tests/test_mkdocs_hooks.py
"""Tests for scripts/mkdocs_hooks.py, which generates build-time-only content
injected into docs pages at `mkdocs build` time (the timezones.md table and
the ai-instructions.md profile dumps), replacing hand-maintained copies that
could silently drift out of sync.
"""

from types import SimpleNamespace
from zoneinfo import available_timezones

from scripts.mkdocs_hooks import (
    TIMEZONE_TABLE_PLACEHOLDER,
    ai_instructions_placeholder,
    generate_ai_instructions_block,
    generate_timezone_table_html,
    get_timezone_rows,
    on_page_markdown,
)
from src.bumpcalver import available_instruction_profiles, get_app_instructions


def test_get_timezone_rows_covers_every_known_timezone():
    rows = get_timezone_rows()
    names = {name for name, _offset in rows}
    assert names == available_timezones()


def test_get_timezone_rows_is_sorted_and_has_utc_offset_format():
    rows = get_timezone_rows()
    names = [name for name, _offset in rows]
    assert names == sorted(names)

    row_by_name = dict(rows)
    assert row_by_name["UTC"] == "UTC+00:00"


def test_generate_timezone_table_html_contains_table_and_every_zone():
    html = generate_timezone_table_html()
    assert '<table id="timezonesTable">' in html
    assert "<script>" in html and "function searchTable()" in html

    for tz_name in ("UTC", "America/New_York", "Asia/Tokyo"):
        assert f"<td>{tz_name}</td>" in html


def _fake_page(src_uri: str):
    return SimpleNamespace(file=SimpleNamespace(src_uri=src_uri))


def test_on_page_markdown_replaces_placeholder_on_timezones_page():
    markdown = f"# Timezones\n\n{TIMEZONE_TABLE_PLACEHOLDER}\n"
    result = on_page_markdown(markdown, _fake_page("timezones.md"), config={}, files=[])

    assert TIMEZONE_TABLE_PLACEHOLDER not in result
    assert '<table id="timezonesTable">' in result
    assert "<td>UTC</td>" in result


def test_on_page_markdown_leaves_other_pages_untouched():
    markdown = f"# Something Else\n\n{TIMEZONE_TABLE_PLACEHOLDER}\n"
    result = on_page_markdown(markdown, _fake_page("index.md"), config={}, files=[])

    assert result == markdown


def test_on_page_markdown_is_a_noop_without_the_placeholder():
    markdown = "# Timezones\n\nNo placeholder here.\n"
    result = on_page_markdown(markdown, _fake_page("timezones.md"), config={}, files=[])

    assert result == markdown


def test_generate_ai_instructions_block_wraps_literal_profile_content():
    block = generate_ai_instructions_block("claude")

    assert block.startswith("````markdown\n")
    assert block.endswith("\n````")
    assert get_app_instructions("claude") in block
    # Confirms the outer fence is 4 backticks specifically because the
    # profile content contains its own 3-backtick TOML fences — if this
    # ever regresses to a 3-backtick outer fence, the inner ones would
    # prematurely close it.
    assert "```toml" in get_app_instructions("claude")


def test_on_page_markdown_replaces_all_profile_placeholders_on_ai_instructions_page():
    markdown = "# AI Assistant Instructions\n\n" + "\n\n".join(
        ai_instructions_placeholder(profile) for profile in available_instruction_profiles()
    )
    result = on_page_markdown(markdown, _fake_page("ai-instructions.md"), config={}, files=[])

    for profile in available_instruction_profiles():
        assert ai_instructions_placeholder(profile) not in result
        assert get_app_instructions(profile) in result


def test_on_page_markdown_ai_instructions_page_without_placeholders_is_untouched():
    markdown = "# AI Assistant Instructions\n\nNothing to substitute here.\n"
    result = on_page_markdown(markdown, _fake_page("ai-instructions.md"), config={}, files=[])

    assert result == markdown
