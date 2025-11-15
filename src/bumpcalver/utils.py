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


def _is_invalid_version_prefix(version: str) -> bool:
    """Check if version has invalid prefixes that indicate non-CalVer patterns."""
    return version.startswith('v') or version.startswith('release')


def _clean_version_suffixes(version: str) -> str:
    """Remove beta/alpha/rc suffixes from version string."""
    return re.sub(r'\.(alpha|beta|rc\d*)$', '', version)


def _validate_date_format(version: str) -> bool:
    """Validate that version looks like a reasonable date format."""
    return bool(re.match(r'^\d+[\.\-/]', version))


def _validate_year_format(year_part: str) -> bool:
    """Validate that the year part looks like a valid year."""
    return bool(re.match(r'^\d{2,4}$', year_part))


def _parse_dot_separated_version(version_parts: list, parts_count: int) -> Optional[tuple]:
    """Parse dot-separated version strings like '25.Q4.001'."""
    if len(version_parts) < parts_count:
        return None

    if len(version_parts) >= 3:
        # Format like "25.Q4.001" -> date="25.Q4", count="001"
        date_str = f"{version_parts[0]}.{version_parts[1]}"
        count_str = version_parts[2]

        if not _validate_year_format(version_parts[0]):
            return None

        return date_str, int(count_str)

    elif len(version_parts) == 2:
        # Format like "25.001" -> date="25", count="001"
        date_str = version_parts[0]
        count_str = version_parts[1]

        if not re.match(r'^\d{2,4}', version_parts[0]):
            return None

        return date_str, int(count_str)

    return None


def _parse_dynamic_version(version: str, version_format: str) -> Optional[tuple]:
    """Parse version using dynamic format rules."""
    if _is_invalid_version_prefix(version):
        return None

    clean_version = _clean_version_suffixes(version)

    # Handle formats without build count (date-only)
    if "{current_date}" in version_format and "{build_count" not in version_format:
        if _validate_date_format(clean_version):
            return clean_version, 0
        return None

    # Handle dot-separated formats
    if "{current_date}" in version_format and "." in version_format:
        parts = version_format.split(".")
        version_parts = clean_version.split(".")
        return _parse_dot_separated_version(version_parts, len(parts))

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
            result = _parse_dynamic_version(version, version_format)
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

def get_build_version(
    file_config: Dict[str, Any], version_format: str, timezone: str, date_format: str
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
    return version_format.format(current_date=current_date, build_count=build_count)
