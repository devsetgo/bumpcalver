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
    # If version_format and date_format are provided, use dynamic parsing
    if version_format and date_format:
        try:
            # Basic validation: reject obviously invalid formats
            if version.startswith('v') or version.startswith('release'):
                # These are typical non-CalVer patterns
                return None

            # Remove any beta/alpha suffixes for parsing
            clean_version = re.sub(r'\.(alpha|beta|rc\d*)$', '', version)

            # For formats that contain {current_date}
            if "{current_date}" in version_format:
                # Check if build_count is NOT in the format (format is just date)
                if "{build_count" not in version_format:
                    # No build count in format, just return the version as date with count 0
                    # But validate it looks like a reasonable date
                    if re.match(r'^\d+[\.\-/]', clean_version):
                        return clean_version, 0
                    else:
                        return None

                # For formats that use dots as separators (like quarter format)
                elif "." in version_format:
                    # Split the version format to understand the structure
                    parts = version_format.split(".")
                    version_parts = clean_version.split(".")

                    if len(version_parts) >= len(parts):
                        # For format like "{current_date}.{build_count:03}", expect 3 parts: year, quarter, count
                        # e.g., "25.Q4.001" -> ["25", "Q4", "001"]
                        if len(version_parts) >= 3:
                            # Assume first two parts form the date, last part is count
                            date_str = f"{version_parts[0]}.{version_parts[1]}"
                            count_str = version_parts[2]

                            # Validate that the first part looks like a year
                            if not re.match(r'^\d{2,4}$', version_parts[0]):
                                return None

                            return date_str, int(count_str)
                        elif len(version_parts) == 2:
                            # If only 2 parts, assume second is count
                            date_str = version_parts[0]
                            count_str = version_parts[1]

                            # Validate that the first part looks like a year or date
                            if not re.match(r'^\d{2,4}', version_parts[0]):
                                return None

                            return date_str, int(count_str)

                # For other formats (e.g., hyphen-separated), fall back to legacy parsing
                # This ensures that formats with hyphens still get proper validation

        except Exception as e:
            # If dynamic parsing fails, print debug info and fall through to legacy parsing
            print(f"Dynamic version parsing failed for '{version}': {e}")
        # Legacy parsing for backward compatibility - Match the version string against the expected format
    match = re.match(r"^(\d{4}-\d{2}-\d{2})(?:-(\d+))?", version)
    if match:
        # Extract the date string and count from the match groups
        date_str = match.group(1)
        count_str = match.group(2) or "0"
        return date_str, int(count_str)
    else:
        # Print an error message if the version string does not match the expected format
        if version_format and date_format:
            print(f"Version '{version}' does not match format '{version_format}' with date format '{date_format}'.")
        else:
            print(f"Version '{version}' does not match expected format 'YYYY-MM-DD' or 'YYYY-MM-DD-XXX'.")
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
