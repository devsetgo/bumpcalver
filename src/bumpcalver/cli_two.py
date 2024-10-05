# # src/bumpcalver/cli.py
# """
# This module provides functions for version management and date handling
# for the bumpcalver library.


# """
# import logging
# import os
# import subprocess
# import sys
# from typing import Any, Dict, List, Optional

# import click
# import toml

# from ._date_functions import default_timezone, get_build_version, get_current_datetime_version
# from .path_parser import get_version_handler, parse_dot_path

# logger = logging.getLogger(__name__)


# # Modify update_version_in_files function in cli.py
# def update_version_in_files(
#     new_version: str, file_configs: List[Dict[str, Any]]
# ) -> List[str]:
#     files_updated: List[str] = []

#     for file_config in file_configs:
#         dot_path: str = file_config["path"]
#         file_path: str = parse_dot_path(dot_path)
#         file_type: str = file_config.get("file_type", "")
#         variable: str = file_config.get("variable", "")

#         if not file_type:
#             print(f"No file_type specified for {file_path}")
#             continue

#         try:
#             handler = get_version_handler(file_type)
#             success = handler.update_version(file_path, variable, new_version)
#             if success:
#                 relative_path: str = os.path.relpath(file_path, start=os.getcwd())
#                 files_updated.append(relative_path)
#         except ValueError as e:
#             print(e)

#     return files_updated


# def load_config() -> Dict[str, Any]:
#     """Load the configuration from pyproject.toml.

#     This function loads the configuration for the bumpcalver tool from the pyproject.toml file.
#     If the file is not found, it uses default configuration values. The configuration includes
#     version format, timezone, file configurations, git tagging, and auto-commit settings.

#     Returns:
#         Dict[str, Any]: A dictionary containing the configuration settings.
#     """
#     config: Dict[str, Any] = {}  # Initialize an empty configuration dictionary

#     if os.path.exists("pyproject.toml"):
#         try:
#             # Open and read the pyproject.toml file
#             with open("pyproject.toml", "r", encoding="utf-8") as f:
#                 pyproject: Dict[str, Any] = toml.load(f)

#             # Extract the bumpcalver configuration from the pyproject.toml file
#             bumpcalver_config: Dict[str, Any] = pyproject.get("tool", {}).get(
#                 "bumpcalver", {}
#             )

#             # Set the configuration values, using defaults if not specified
#             config["version_format"]: str = bumpcalver_config.get(
#                 "version_format", "{current_date}-{build_count:03}"
#             )
#             config["timezone"]: str = bumpcalver_config.get(
#                 "timezone", default_timezone
#             )
#             config["file_configs"]: list = bumpcalver_config.get("file", [])
#             config["git_tag"]: bool = bumpcalver_config.get("git_tag", False)
#             config["auto_commit"]: bool = bumpcalver_config.get("auto_commit", False)
#         except toml.TomlDecodeError as e:
#             # Print an error message and exit if there is a TOML decoding error
#             print(f"Error parsing pyproject.toml: {e}")
#             sys.exit(1)
#     else:
#         # Print a message if the pyproject.toml file is not found and use default configuration
#         print("pyproject.toml not found. Using default configuration.")

#     return config


# def create_git_tag(version: str, files_to_commit: List[str], auto_commit: bool) -> None:
#     """Create a Git tag for the specified version.

#     This function checks if the current directory is inside a Git repository,
#     optionally commits the specified files, and creates a Git tag for the given version.

#     Args:
#         version (str): The version string to use for the Git tag.
#         files_to_commit (List[str]): A list of file paths to commit.
#         auto_commit (bool): Whether to automatically commit the specified files.

#     Returns:
#         None
#     """
#     try:
#         # Check if in a Git repository
#         subprocess.run(
#             ["git", "rev-parse", "--is-inside-work-tree"],
#             check=True,
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL,
#         )
#     except subprocess.CalledProcessError:
#         # Print a message and return if not in a Git repository
#         print("Not a Git repository. Skipping Git tagging.")
#         return

#     try:
#         if auto_commit:
#             if files_to_commit:
#                 # Stage only the updated files
#                 subprocess.run(["git", "add"] + files_to_commit, check=True)
#                 # Commit changes with a message
#                 commit_message: str = f"Bump version to {version}"
#                 subprocess.run(["git", "commit", "-m", commit_message], check=True)
#             else:
#                 # Print a message if no files were updated
#                 print("No files were updated. Skipping Git commit.")
#         else:
#             # Print a message if auto-commit is disabled
#             print("Auto-commit is disabled. Tagging current commit.")

#         # Create Git tag with the specified version
#         subprocess.run(["git", "tag", version], check=True)
#         print(f"Created Git tag '{version}'")
#     except subprocess.CalledProcessError as e:
#         # Print an error message if a Git operation fails
#         print(f"Error during Git operations: {e}")


# # src/bumpcalver/cli.py


# @click.command()
# @click.option("--beta", is_flag=True, help="Use beta versioning")
# @click.option("--rc", is_flag=True, help="Use rc versioning")
# @click.option("--build", is_flag=True, help="Use build count versioning")
# @click.option(
#     "--timezone",
#     help="Timezone for date calculations (default: value from config or America/New_York)",
# )
# @click.option(
#     "--git-tag/--no-git-tag", default=None, help="Create a Git tag with the new version"
# )
# @click.option(
#     "--auto-commit/--no-auto-commit",
#     default=None,
#     help="Automatically commit changes when creating a Git tag",
# )
# def main(
#     beta: bool,
#     rc: bool,
#     build: bool,
#     timezone: Optional[str],
#     git_tag: Optional[bool],
#     auto_commit: Optional[bool],
# ) -> None:
#     """Main function for the bumpcalver CLI tool.

#     This function handles the command-line interface for the bumpcalver tool. It loads the configuration,
#     determines the new version based on the provided options, updates the version in specified files,
#     and optionally creates a Git tag and commits the changes.

#     Args:
#         beta (bool): Flag to use beta versioning.
#         build (bool): Flag to use build count versioning.
#         timezone (Optional[str]): Timezone for date calculations.
#         git_tag (Optional[bool]): Flag to create a Git tag with the new version.
#         auto_commit (Optional[bool]): Flag to automatically commit changes when creating a Git tag.

#     Returns:
#         None
#     """
#     # Load the configuration from pyproject.toml
#     config: Dict[str, Any] = load_config()
#     version_format: str = config.get(
#         "version_format", "{current_date}-{build_count:03}"
#     )
#     file_configs: List[Dict[str, Any]] = config.get("file_configs", [])
#     config_timezone: str = config.get("timezone", default_timezone)
#     config_git_tag: bool = config.get("git_tag", False)
#     config_auto_commit: bool = config.get("auto_commit", False)

#     if not file_configs:
#         print("No files specified in the configuration.")
#         return

#     # Use the timezone from the command line if provided; otherwise, use config
#     timezone = timezone or config_timezone

#     # Determine whether to create a Git tag
#     if git_tag is None:
#         git_tag = config_git_tag

#     # Determine whether to auto-commit changes
#     if auto_commit is None:
#         auto_commit = config_auto_commit

#     # Adjust the base directory
#     project_root: str = os.getcwd()
#     # Update file paths to be absolute
#     for file_config in file_configs:
#         file_config["path"] = os.path.join(project_root, file_config["path"])

#     try:
#         # Get the new version
#         if build:
#             # Use the first file config for getting the build count
#             init_file_config: Dict[str, Any] = file_configs[0]
#             new_version: str = get_build_version(
#                 init_file_config, version_format, timezone
#             )
#         else:
#             new_version = get_current_datetime_version(timezone)

#         if beta:
#             new_version += "-beta"

#         # Update the version in the specified files
#         files_updated: List[str] = update_version_in_files(new_version, file_configs)

#         # Create a Git tag if enabled
#         if git_tag:
#             create_git_tag(new_version, files_updated, auto_commit)

#         print(f"Updated version to {new_version} in specified files.")
#     except (ValueError, KeyError) as e:
#         print(f"Error generating version: {e}")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()
