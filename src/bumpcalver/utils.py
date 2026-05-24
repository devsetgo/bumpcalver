"""
Utility functions for BumpCalver.

This module provides various utility functions used by BumpCalver for tasks such as
parsing dot paths, parsing version strings, and getting the current date with timezone support.

Functions:
    parse_dot_path: Parses a dot-separated path and converts it to a file path.
    parse_version: Parses a version string and returns a tuple of date and count.
    get_current_date: Returns the current date in the specified timezone.

Constants:
    default_timezone: The default timezone used for date calculations.

Example:
    To parse a dot-separated path:
        file_path = parse_dot_path("src.module", "python")

    To parse a version string:
        version_info = parse_version("2023-10-05-001")

    To get the current date in a specific timezone:
        current_date = get_current_date("Europe/London")
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .handlers import get_version_handler

default_timezone: str = "America/New_York"


def parse_dot_path(dot_path: str, file_type: str) -> str:
    """Parses a dot-separated path and converts it to a file path.

    This function converts a dot-separated path to a file path. If the input path
    is already a valid file path (contains '/' or '\\' or is an absolute path),
    it returns the input path as is. For Python files, it ensures the path ends
    with '.py'.

    Args:
        dot_path (str): The dot-separated path to parse.
        file_type (str): The type of the file (e.g., "python").

    Returns:
        str: The converted file path.

    Example:
        file_path = parse_dot_path("src.module", "python")
    """
    # Check if the input path is already a valid file path
    if "/" in dot_path or "\\" in dot_path or os.path.isabs(dot_path):
        return dot_path

    # For Python files, ensure the path ends with '.py'
    if file_type == "python" and not dot_path.endswith(".py"):
        return dot_path.replace(".", os.sep) + ".py"

    # Return the converted path
    return dot_path


_SEMVER_PLACEHOLDERS = frozenset({"{major}", "{minor}", "{patch}"})
_CURRENT_DATE_KEY = "{current_date}"
_TWO_DIGITS = r"\d{2}"

_STRFTIME_CODES = [
    ("%-m", r"\d{1,2}"),
    ("%-d", r"\d{1,2}"),
    ("%Y",  r"\d{4}"),
    ("%y",  _TWO_DIGITS),
    ("%m",  _TWO_DIGITS),
    ("%d",  _TWO_DIGITS),
    ("%j",  r"\d{3}"),
    ("%H",  _TWO_DIGITS),
    ("%M",  _TWO_DIGITS),
    ("%S",  _TWO_DIGITS),
    ("%q",  r"\d"),
]


def _is_hybrid_format(version_format: str) -> bool:
    """Return True if version_format contains any semantic version placeholders."""
    return any(ph in version_format for ph in _SEMVER_PLACEHOLDERS)


def _date_format_to_regex(date_format: str) -> str:
    """Convert a strftime date_format string to a regex fragment."""
    result = re.escape(date_format)
    for code, pattern in _STRFTIME_CODES:
        result = result.replace(re.escape(code), pattern)
    return result


def _parse_hybrid_version(
    version: str, version_format: str, date_format: str
) -> Optional[tuple]:
    """Parse a hybrid semantic+calendar version string.

    Returns (date_str, build_count) or None.
    """
    temp = re.sub(r'\{build_count:[^}]+\}', "__BUILD_SPEC__", version_format)
    temp = (temp
            .replace("{major}",        "__MAJOR__")
            .replace("{minor}",        "__MINOR__")
            .replace("{patch}",        "__PATCH__")
            .replace(_CURRENT_DATE_KEY, "__DATE__")
            .replace("{build_count}",  "__BUILD__"))

    pattern = re.escape(temp)
    date_rx = _date_format_to_regex(date_format)
    pattern = (pattern
               .replace("__MAJOR__",      r"(?P<major>\d+)")
               .replace("__MINOR__",      r"(?P<minor>\d+)")
               .replace("__PATCH__",      r"(?P<patch>\d+)")
               .replace("__DATE__",       f"(?P<current_date>{date_rx})")
               .replace("__BUILD_SPEC__", r"(?P<build_count>\d+)")
               .replace("__BUILD__",      r"(?P<build_count>\d+)"))

    clean = _clean_version_suffixes(version)
    m = re.fullmatch(pattern, clean)
    if not m:
        return None

    date_str = m.group("current_date")
    try:
        count = int(m.group("build_count"))
    except (IndexError, ValueError):
        count = 0
    return date_str, count


def _is_invalid_version_prefix(version: str) -> bool:
    """Check if version has invalid prefixes that indicate non-CalVer patterns."""
    return version.startswith(('v', 'release'))


def _clean_version_suffixes(version: str) -> str:
    """Remove pre-release suffixes from a version string.

    Handles dot-prefixed forms (.beta, .rc1) and PEP 440 attached forms
    (b1, rc2, a1) where letters follow immediately after a digit.
    """
    cleaned = re.sub(r'\.(alpha|beta|rc\d*|release)$', '', version)
    if cleaned != version:
        return cleaned
    # PEP 440 attached directly after a digit: b1, a1, rc1, etc.
    return re.sub(r'(?<=\d)[a-zA-Z]+\d*$', '', version)


def apply_prerelease_suffix(
    base_version: str,
    suffix_format: str,
    current_raw_version: str = "",
) -> str:
    """Apply a pre-release suffix to *base_version*, honouring ``{xxx_count}`` placeholders.

    If *suffix_format* contains no placeholder the literal string is appended.
    When a placeholder is present the count is derived from *current_raw_version*:
    if it starts with *base_version* + the suffix prefix the existing count is
    incremented; otherwise the count starts at 1.
    """
    count_match = re.search(r'\{[^}]+\}', suffix_format)
    if not count_match:
        return base_version + suffix_format

    literal_prefix = suffix_format[: count_match.start()]
    literal_after = suffix_format[count_match.end() :]

    count = 1
    if current_raw_version:
        pattern = (
            re.escape(base_version)
            + re.escape(literal_prefix)
            + r'(\d+)'
            + re.escape(literal_after)
            + '$'
        )
        m = re.match(pattern, current_raw_version)
        if m:
            count = int(m.group(1)) + 1

    return f"{base_version}{literal_prefix}{count}{literal_after}"


def _validate_date_format(version: str) -> bool:
    """Validate that version looks like a reasonable date format."""
    return bool(re.match(r'^\d+[\.\-/]', version))


def _validate_year_format(year_part: str) -> bool:
    """Validate that the year part looks like a valid year."""
    # Accept common CalVer leading segments:
    # - YY (e.g. 24)
    # - YYYY (e.g. 2024)
    # - YYMMDD (e.g. 241207)
    # - YYYYMMDD (e.g. 20241207)
    # Keep rejecting 1-digit segments like "1" (SemVer-ish patterns).
    return bool(re.match(r'^\d{2}(?:\d{2}){0,3}$', year_part))


def _parse_dot_separated_version(version_parts: list[str]) -> Optional[tuple[str, int]]:
    """Parse dot-separated version strings like '26.1.28.1' or '25.Q4.001'."""
    # We treat the last segment as the build count and everything before it
    # as the date portion. This supports date formats that themselves contain
    # dots (e.g. %y.%-m.%-d -> 26.1.28) as well as quarter formats (25.Q4).
    if len(version_parts) < 2:
        return None  # pragma: no cover

    if not _validate_year_format(version_parts[0]):
        return None

    count_str = version_parts[-1]
    try:
        count = int(count_str)
    except ValueError:
        return None  # pragma: no cover

    date_str = ".".join(version_parts[:-1])
    return date_str, count


def _parse_dynamic_version(version: str, version_format: str, date_format: str = "") -> Optional[tuple]:
    """Parse version using dynamic format rules."""
    if _is_hybrid_format(version_format):
        return _parse_hybrid_version(version, version_format, date_format)

    if _is_invalid_version_prefix(version):
        return None

    clean_version = _clean_version_suffixes(version)

    # Handle formats without build count (date-only)
    if _CURRENT_DATE_KEY in version_format and "{build_count" not in version_format:
        if _validate_date_format(clean_version):
            return clean_version, 0
        return None # pragma: no cover

    # Handle dot-separated formats
    if _CURRENT_DATE_KEY in version_format and "." in version_format:
        version_parts = clean_version.split(".")
        return _parse_dot_separated_version(version_parts)

    return None


def _parse_legacy_version(version: str) -> Optional[tuple]:
    """Parse version using legacy YYYY-MM-DD format."""
    match = re.match(r"^(\d{4}-\d{2}-\d{2})(?:-(\d+))?", version)
    if match:
        date_str = match.group(1)
        count_str = match.group(2) or "0"
        return date_str, int(count_str)
    return None


def _print_version_error(version: str, version_format: Optional[str], date_format: Optional[str]) -> None:
    """Print appropriate error message for version parsing failure."""
    if version_format and date_format:
        print(f"Version '{version}' does not match format '{version_format}' with date format '{date_format}'.")
    else:
        print(f"Version '{version}' does not match expected format 'YYYY-MM-DD' or 'YYYY-MM-DD-XXX'.")


def parse_version(version: str, version_format: Optional[str] = None, date_format: Optional[str] = None) -> Optional[tuple]:
    """Parses a version string and returns a tuple of date and count.

    This function can parse version strings in various formats. If version_format and date_format
    are provided, it will use them to dynamically parse the version. Otherwise, it falls back
    to the legacy 'YYYY-MM-DD-XXX' format for backwards compatibility.

    Args:
        version (str): The version string to parse.
        version_format (str, optional): The format string used to create the version (e.g., "{current_date}.{build_count:03}")
        date_format (str, optional): The date format string (e.g., "%y.Q%q")

    Returns:
        Optional[tuple]: A tuple containing the date string and count, or None if the version string is invalid.

    Examples:
        version_info = parse_version("2023-10-05-001")  # Legacy format
        version_info = parse_version("25.Q4.001", "{current_date}.{build_count:03}", "%y.Q%q")  # Custom format
    """
    # Try dynamic parsing if format parameters are provided
    if version_format and date_format:
        try:
            result = _parse_dynamic_version(version, version_format, date_format or "")
            if result is not None:
                return result
        except Exception as e:
            print(f"Dynamic version parsing failed for '{version}': {e}")

    # Fall back to legacy parsing
    result = _parse_legacy_version(version)
    if result is not None:
        return result

    # Print error if no parsing method succeeded
    _print_version_error(version, version_format, date_format)
    return None


def get_current_date(
    timezone: str = default_timezone, date_format: str = "%Y.%m.%d"
) -> str:
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        print(f"Unknown timezone '{timezone}'. Using default '{default_timezone}'.")
        tz = ZoneInfo(default_timezone)
    return datetime.now(tz).strftime(date_format)


def get_current_datetime_version(
    timezone: str = default_timezone, date_format: str = "%Y.%m.%d"
) -> str:
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        print(f"Unknown timezone '{timezone}'. Using default '{default_timezone}'.")
        tz = ZoneInfo(default_timezone)
    now = datetime.now(tz)

    # Handle quarter formatting
    if "%q" in date_format:
        quarter = (now.month - 1) // 3 + 1
        date_format = date_format.replace("%q", str(quarter))

    return now.strftime(date_format)

def update_semantic_in_config(key: str, value: int) -> bool:
    """Update major/minor/patch integer in pyproject.toml or bumpcalver.toml."""
    for config_file in ("pyproject.toml", "bumpcalver.toml"):
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
            pattern = rf'^({re.escape(key)}\s*=\s*)\d+'
            new_content = re.sub(pattern, rf'\g<1>{value}', content, flags=re.MULTILINE)
            if new_content != content:
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True
    return False


def get_build_version(
    file_config: Dict[str, Any],
    version_format: str,
    timezone: str,
    date_format: str,
    major: int = 0,
    minor: int = 0,
    patch: int = 0,
) -> str:
    """Returns the build version string based on the provided file configuration.

    This function reads the current version from the specified file, increments the build count
    if the date matches the current date, and returns the formatted build version string.

    Args:
        file_config (Dict[str, Any]): A dictionary containing file configuration details.
            - "path" (str): The path to the file.
            - "file_type" (str): The type of the file (e.g., "python", "toml", "yaml", "json", "xml", "dockerfile", "makefile").
            - "variable" (str, optional): The variable name that holds the version string.
            - "directive" (str, optional): The directive for Dockerfile (e.g., "ARG" or "ENV").
        version_format (str): The format string for the version.
        timezone (str): The timezone to use for date calculations.
        date_format (str): The format string for the date.

    Returns:
        str: The formatted build version string.

    Example:
        file_config = {
            "path": "version.py",
            "file_type": "python",
            "variable": "__version__"
        }
        build_version = get_build_version(file_config, "{current_date}-{build_count:03}", "America/New_York", "%Y.%m.%d")
    """
    file_path = file_config["path"]
    file_type = file_config.get("file_type", "")
    variable = file_config.get("variable", "")
    directive = file_config.get("directive", "")

    # Get the current date in the specified timezone and format
    current_date = get_current_datetime_version(timezone, date_format)
    build_count = 1  # Default build count

    try:
        # Get the appropriate version handler for the file type
        handler = get_version_handler(file_type)
        if directive:
            # Read the version using the directive if provided
            version = handler.read_version(file_path, variable, directive=directive)
        else:
            # Read the version without the directive
            version = handler.read_version(file_path, variable)

        if version:
            # Parse the version string with the format information
            parsed_version = parse_version(version, version_format, date_format)
            if parsed_version:
                last_date, last_count = parsed_version
                if last_date == current_date:
                    # Increment the build count if the date matches the current date
                    build_count = last_count + 1
                else:
                    build_count = 1
            else:
                print(f"File '{file_path}': Version '{version}' does not match expected format. Expected format: '{version_format}' with date format: '{date_format}'.")
                build_count = 1
        else:
            print(f"File '{file_path}': Could not read version. Starting new versioning with format 'YYYY-MM-DD-XXX'.")
            build_count = 1
    except Exception as e:
        print(f"File '{file_path}': Error reading version - {e}. Starting new versioning with format 'YYYY-MM-DD-XXX'.")
        build_count = 1

    # Return the formatted build version string
    return version_format.format(
        current_date=current_date,
        build_count=build_count,
        major=major,
        minor=minor,
        patch=patch,
    )
