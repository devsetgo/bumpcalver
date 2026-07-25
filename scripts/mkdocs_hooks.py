"""mkdocs build hooks, registered via mkdocs.yml's `hooks:` key.

Single source of truth for the timezone reference table injected into
docs/timezones.md at `mkdocs build` time. Previously this ~600-row table was
hand-copied into both docs/timezones.md *and* a separate, unreferenced
docs/timezones_table.html, with no mechanism keeping the two in sync (see
IMPROVEMENTS.md §3.3). Generating it here means there is exactly one copy of
this data, it is always current for whatever Python/tzdata built the docs,
and nothing needs to be hand-regenerated when timezones change upstream.
"""

from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

TIMEZONE_TABLE_PLACEHOLDER = "<!-- TIMEZONE_TABLE -->"


def get_timezone_rows() -> list[tuple[str, str]]:
    """Return (timezone_name, utc_offset_str) pairs for every known zone, sorted by name."""
    rows = []
    for tz_name in sorted(available_timezones()):
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        offset = tz.utcoffset(now)

        if offset is None:  # pragma: no cover
            # Defensive: ZoneInfo.utcoffset() always returns a real offset
            # for a valid zone key in practice, but the return type is
            # formally Optional per the tzinfo interface.
            offset_str = "Unknown"
        else:
            total_seconds = offset.total_seconds()
            sign = "+" if total_seconds >= 0 else "-"
            total_seconds = abs(total_seconds)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            offset_str = f"UTC{sign}{int(hours):02d}:{int(minutes):02d}"

        rows.append((tz_name, offset_str))
    return rows


def generate_timezone_table_html() -> str:
    """Render the search box, table, and search JS as one HTML fragment."""
    row_html = "\n\n".join(
        f"        <tr>\n            <td>{name}</td>\n            <td>{offset}</td>\n        </tr>"
        for name, offset in get_timezone_rows()
    )
    return f"""<input type="text" id="searchInput" onkeyup="searchTable()" placeholder="Search for timezones..">

<table id="timezonesTable">
    <thead>
        <tr>
            <th>Timezone</th>
            <th>UTC Offset</th>
        </tr>
    </thead>
    <tbody>

{row_html}

    </tbody>
</table>

<script>
function searchTable() {{
    var input, filter, table, tr, td, i, j, txtValue;
    input = document.getElementById("searchInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("timezonesTable");
    tr = table.getElementsByTagName("tr");

    for (i = 1; i < tr.length; i++) {{
        tr[i].style.display = "none";
        td = tr[i].getElementsByTagName("td");
        for (j = 0; j < td.length; j++) {{
            if (td[j]) {{
                txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                    tr[i].style.display = "";
                    break;
                }}
            }}
        }}
    }}
}}
</script>
"""


def on_page_markdown(markdown, page, config, files):
    """mkdocs event hook: substitute the placeholder in docs/timezones.md only."""
    if page.file.src_uri == "timezones.md" and TIMEZONE_TABLE_PLACEHOLDER in markdown:
        return markdown.replace(TIMEZONE_TABLE_PLACEHOLDER, generate_timezone_table_html())
    return markdown
