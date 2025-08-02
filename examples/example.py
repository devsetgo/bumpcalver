__version__ = "2025.8.2.1"
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

# Prepare a list to store time zone information
timezones = []

for tz_name in sorted(available_timezones()):
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    offset = tz.utcoffset(now)

    if offset is None:
        offset_str = "Unknown"
    else:
        total_seconds = offset.total_seconds()
        sign = "+" if total_seconds >= 0 else "-"
        total_seconds = abs(total_seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        offset_str = f"UTC{sign}{int(hours):02d}:{int(minutes):02d}"

    timezones.append((tz_name, offset_str))

# Generate HTML table
html_table = """
<input type="text" id="searchInput" onkeyup="searchTable()" placeholder="Search for timezones..">

<table id="timezonesTable">
    <thead>
        <tr>
            <th>Timezone</th>
            <th>UTC Offset</th>
        </tr>
    </thead>
    <tbody>
"""

for tz_name, offset_str in timezones:
    html_table += f"""
        <tr>
            <td>{tz_name}</td>
            <td>{offset_str}</td>
        </tr>
    """

html_table += """
    </tbody>
</table>

<script>
function searchTable() {
    var input, filter, table, tr, td, i, j, txtValue;
    input = document.getElementById("searchInput");
    filter = input.value.toUpperCase();
    table = document.getElementById("timezonesTable");
    tr = table.getElementsByTagName("tr");

    for (i = 1; i < tr.length; i++) {
        tr[i].style.display = "none";
        td = tr[i].getElementsByTagName("td");
        for (j = 0; j < td.length; j++) {
            if (td[j]) {
                txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                    break;
                }
            }
        }
    }
}
</script>
"""

# Save the HTML table to a text file
with open("timezones_table.html", "w") as file:
    file.write(html_table)
