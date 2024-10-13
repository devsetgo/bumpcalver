import os
import re
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .handlers import get_version_handler

default_timezone: str = "America/New_York"


def parse_dot_path(dot_path: str, file_type: str) -> str:
    if "/" in dot_path or "\\" in dot_path or os.path.isabs(dot_path):
        return dot_path
    if file_type == "python" and not dot_path.endswith(".py"):
        return dot_path.replace(".", os.sep) + ".py"
    return dot_path


def parse_version(version: str) -> Optional[tuple]:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})(?:-(\d+))?", version)
    if match:
        date_str = match.group(1)
        count_str = match.group(2) or "0"
        return date_str, int(count_str)
    else:
        print(f"Version '{version}' does not match expected format.")
        return None


def get_current_date(timezone: str = default_timezone) -> str:
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        print(f"Unknown timezone '{timezone}'. Using default '{default_timezone}'.")
        tz = ZoneInfo(default_timezone)
    return datetime.now(tz).strftime("%Y-%m-%d")


def get_current_datetime_version(timezone: str = default_timezone) -> str:
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        print(f"Unknown timezone '{timezone}'. Using default '{default_timezone}'.")
        tz = ZoneInfo(default_timezone)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def get_build_version(
    file_config: Dict[str, Any], version_format: str, timezone: str
) -> str:

    file_path = file_config["path"]
    file_type = file_config.get("file_type", "")
    variable = file_config.get("variable", "")
    directive = file_config.get("directive", "")

    current_date = get_current_datetime_version(timezone)
    build_count = 1  # Default build count

    try:
        handler = get_version_handler(file_type)
        if directive:
            version = handler.read_version(file_path, variable, directive=directive)
        else:
            version = handler.read_version(file_path, variable)

        if version:
            parsed_version = parse_version(version)
            if parsed_version:
                last_date, last_count = parsed_version
                if last_date == current_date:
                    build_count = last_count + 1
                else:
                    build_count = 1
            else:
                print(f"Version '{version}' does not match expected format.")
                build_count = 1
        else:
            print(f"Could not read version from {file_path}. Starting new versioning.")
            build_count = 1
    except Exception as e:
        print(f"Error reading version from {file_path}: {e}")
        build_count = 1

    return version_format.format(current_date=current_date, build_count=build_count)
