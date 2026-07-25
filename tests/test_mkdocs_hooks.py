# tests/test_mkdocs_hooks.py
"""Tests for scripts/mkdocs_hooks.py, which generates the timezone table

injected into docs/timezones.md at `mkdocs build` time (see IMPROVEMENTS.md
§3.3 — this replaced two hand-maintained, always-driftable copies of the
same ~600-row table with one generated-on-demand copy).
"""

from types import SimpleNamespace
from zoneinfo import available_timezones

from scripts.mkdocs_hooks import (
    TIMEZONE_TABLE_PLACEHOLDER,
    generate_timezone_table_html,
    get_timezone_rows,
    on_page_markdown,
)


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
