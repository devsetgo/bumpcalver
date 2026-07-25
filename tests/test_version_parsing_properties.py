# tests/test_version_parsing_properties.py
"""Property-based tests for the version-format parsing machinery.

Complements the specific-example tests in test_calver_comprehensive.py and
test_hybrid_versioning.py with broader, randomized coverage: for a fixed set
of format templates already exercised elsewhere in the suite, any valid
build_count/date/semver combination plugged into that template must survive
a format -> parse round trip. Hypothesis's shrinking reports the smallest
failing example on a failure, which is far more actionable than debugging
one of a handful of hand-picked cases.

Deliberately scoped to a *fixed* set of format templates rather than
generating random format strings too — the format-string-to-regex
translation has inherent ambiguity for some format combinations (that's a
property of the format, not a bug), so randomizing format strings as well
would produce spurious failures unrelated to real parsing bugs.
"""

from datetime import date

from hypothesis import given, settings
from hypothesis import strategies as st

from src.bumpcalver.utils import parse_version

_REASONABLE_DATES = st.dates(min_value=date(2000, 1, 1), max_value=date(2099, 12, 31))
_BUILD_COUNTS = st.integers(min_value=0, max_value=9999)
_SEMVER_PARTS = st.integers(min_value=0, max_value=99)


@given(the_date=_REASONABLE_DATES, build_count=_BUILD_COUNTS)
@settings(max_examples=200)
def test_dot_separated_calver_round_trips(the_date, build_count):
    version_format = "{current_date}.{build_count:03}"
    date_format = "%Y.%m.%d"
    date_str = the_date.strftime(date_format)
    version_string = version_format.format(current_date=date_str, build_count=build_count)

    result = parse_version(version_string, version_format, date_format)

    assert result == (date_str, build_count)


@given(the_date=_REASONABLE_DATES, build_count=_BUILD_COUNTS)
@settings(max_examples=200)
def test_dash_separated_calver_with_dot_date_round_trips(the_date, build_count):
    # Regression coverage for the bug fixed alongside these tests (see
    # IMPROVEMENTS.md Testing §4.5): bumpcalver's own CLI built-in
    # zero-config defaults are exactly this combination
    # (version_format="{current_date}-{build_count:03}",
    # date_format="%Y.%m.%d"), and it used to never round-trip at all.
    version_format = "{current_date}-{build_count:03}"
    date_format = "%Y.%m.%d"
    date_str = the_date.strftime(date_format)
    version_string = version_format.format(current_date=date_str, build_count=build_count)

    result = parse_version(version_string, version_format, date_format)

    assert result == (date_str, build_count)


@given(
    major=_SEMVER_PARTS,
    minor=_SEMVER_PARTS,
    patch=_SEMVER_PARTS,
    the_date=_REASONABLE_DATES,
    build_count=_BUILD_COUNTS,
)
@settings(max_examples=200)
def test_hybrid_semver_calendar_round_trips(major, minor, patch, the_date, build_count):
    version_format = "{major}.{minor}.{patch}-{current_date}.{build_count:03}"
    date_format = "%Y%m%d"
    date_str = the_date.strftime(date_format)
    version_string = version_format.format(
        major=major, minor=minor, patch=patch, current_date=date_str, build_count=build_count
    )

    result = parse_version(version_string, version_format, date_format)

    assert result == (date_str, build_count)
