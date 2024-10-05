# import logging
# from datetime import datetime
# from typing import Dict, Optional
# from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# from .cli import get_version_handler

# default_timezone: str = "America/New_York"


# def parse_version(version: str) -> Optional[tuple]:
#     """
#     Parses the version to extract the date and count.

#     Args:
#         version (str): The version string.

#     Returns:
#         Optional[tuple]: A tuple of (date, count) if successful, otherwise None.
#     """
#     try:
#         date_str, count_str = version.split("-")
#         return date_str, int(count_str)
#     except ValueError:
#         return None


# def get_current_date(timezone: str = default_timezone) -> str:
#     """Get the current date in a specified timezone.

#     This function returns the current date formatted as 'YYYY-MM-DD' in the specified timezone.
#     If the specified timezone is not found, it defaults to 'America/New_York'.

#     Args:
#         timezone (str): The timezone to use. Defaults to 'America/New_York'.

#     Returns:
#         str: The current date in the specified timezone formatted as 'YYYY-MM-DD'.
#     """
#     try:
#         # Attempt to get the specified timezone
#         tz = ZoneInfo(timezone)
#     except ZoneInfoNotFoundError:
#         # If the timezone is not found, print a message and use the default timezone
#         print(f"Unknown timezone '{timezone}'. Using default '{default_timezone}'.")
#         tz = ZoneInfo(default_timezone)

#     # Get the current date in the specified timezone and format it as 'YYYY-MM-DD'
#     return datetime.now(tz).strftime("%Y-%m-%d")


# def get_current_datetime_version(timezone: str = default_timezone) -> str:
#     """
#     Get the current date as a version string.

#     Args:
#         timezone (str): The timezone to use for generating the version.

#     Returns:
#         str: A version string based on the current date.
#     """
#     now = datetime.now()
#     return now.strftime("%Y%m%d")


# # Update get_build_version function in _date_functions.py


# def get_build_version(
#     file_config: Dict[str, Any], version_format: str, timezone: str
# ) -> str:
#     """
#     Generates the build version based on the current date and the build count.

#     Args:
#         file_config (Dict[str, Any]): The configuration of the file containing the current version.
#         version_format (str): The format to use for the new version.
#         timezone (str): The timezone to use for generating the version.

#     Returns:
#         str: The generated build version.
#     """
#     # Convert dot-separated path to actual file path if necessary
#     file_path = file_config["path"]
#     file_type = file_config.get("file_type", "")
#     variable = file_config.get("variable", "")

#     # Get the current date for versioning
#     current_date = get_current_datetime_version(timezone)
#     build_count = 1  # Default build count

#     try:
#         # Use the appropriate handler for reading the version
#         handler = get_version_handler(file_type)
#         version = handler.read_version(file_path, variable)

#         if version:
#             # Parse the version to get the last date and count
#             parsed_version = parse_version(version)
#             if parsed_version:
#                 last_date, last_count = parsed_version
#                 if last_date == current_date:
#                     build_count = last_count + 1
#         else:
#             logging.warning(
#                 f"Could not read version from {file_path}. Starting new versioning."
#             )
#     except Exception as e:
#         logging.error(f"Error reading version from {file_path}: {e}")
#         build_count = 1

#     # Return the formatted build version
#     return version_format.format(current_date=current_date, build_count=build_count)
