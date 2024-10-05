# src/bumpcalver/cli.py
"""
This module provides functions for version management and date handling
for the bumpcalver library.
"""
import json
import logging
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import click
import toml
import yaml

# from ._date_functions import default_timezone, get_build_version, get_current_datetime_version
# from .path_parser import get_version_handler, parse_dot_path

logger = logging.getLogger(__name__)


default_timezone: str = "America/New_York"


def update_version_in_files(
    new_version: str, file_configs: List[Dict[str, Any]]
) -> List[str]:
    """
    Update version in the specified files.

    Args:
        new_version (str): The new version to set.
        file_configs (List[Dict[str, Any]]): List of file configurations.

    Returns:
        List[str]: List of updated files.
    """
    files_updated: List[str] = []

    for file_config in file_configs:
        file_path: str = file_config["path"]  # Already parsed in load_config
        file_type: str = file_config.get("file_type", "")
        variable: str = file_config.get("variable", "")

        if not file_type:
            print(f"No file_type specified for {file_path}")
            continue

        try:
            handler = get_version_handler(file_type)
            success = handler.update_version(file_path, variable, new_version)
            if success:
                relative_path: str = os.path.relpath(file_path, start=os.getcwd())
                files_updated.append(relative_path)
        except ValueError as e:
            print(e)

    return files_updated


def load_config() -> Dict[str, Any]:
    """Load the configuration from pyproject.toml."""
    config: Dict[str, Any] = {}

    if os.path.exists("pyproject.toml"):
        try:
            # Open and read the pyproject.toml file
            with open("pyproject.toml", "r", encoding="utf-8") as f:
                pyproject: Dict[str, Any] = toml.load(f)

            # Extract the bumpcalver configuration from the pyproject.toml file
            bumpcalver_config: Dict[str, Any] = pyproject.get("tool", {}).get("bumpcalver", {})

            # Set the configuration values, using defaults if not specified
            config["version_format"] = bumpcalver_config.get("version_format", "{current_date}-{build_count:03}")
            config["timezone"] = bumpcalver_config.get("timezone", default_timezone)
            config["file_configs"] = bumpcalver_config.get("file", [])
            config["git_tag"] = bumpcalver_config.get("git_tag", False)
            config["auto_commit"] = bumpcalver_config.get("auto_commit", False)

            # Print paths for debugging
            for file_config in config["file_configs"]:
                original_path = file_config["path"]
                file_config["path"] = parse_dot_path(file_config["path"])
                print(f"Original path: {original_path} -> Converted path: {file_config['path']}")  # Debug print

        except toml.TomlDecodeError as e:
            print(f"Error parsing pyproject.toml: {e}")
            sys.exit(1)
    else:
        print("pyproject.toml not found. Using default configuration.")

    return config


def create_git_tag(version: str, files_to_commit: List[str], auto_commit: bool) -> None:
    """Create a Git tag for the specified version."""
    try:
        # Check if the Git tag already exists
        tag_check = subprocess.run(
            ["git", "tag", "-l", version], capture_output=True, text=True
        )
        if version in tag_check.stdout.splitlines():
            print(f"Tag '{version}' already exists. Skipping tag creation.")
            return

        # Check if in a Git repository
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.PIPE,
        )

        # Auto-commit if enabled
        if auto_commit:
            subprocess.run(["git", "add"] + files_to_commit, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Bump version to {version}"], check=True
            )

        # Create Git tag
        subprocess.run(["git", "tag", version], check=True)
        print(f"Created Git tag '{version}'")
    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")


class VersionHandler(ABC):
    @abstractmethod
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        pass

    @abstractmethod
    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        pass


class PythonVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        version_pattern = re.compile(
            rf'^\s*{re.escape(variable)}\s*=\s*["\'](.+?)["\']\s*$', re.MULTILINE
        )
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            match = version_pattern.search(content)
            return match.group(1) if match else None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        version_pattern = re.compile(
            rf'^(\s*{re.escape(variable)}\s*=\s*)(["\'])(.+?)(["\'])\s*$', re.MULTILINE
        )
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            new_content, num_subs = version_pattern.subn(
                rf'\1"\3{new_version}\4"', content
            )
            if num_subs > 0:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                return True
            return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class TomlVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = toml.load(file)
                if variable in toml_content.get("project", {}):
                    return toml_content["project"][variable]
            return None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = toml.load(file)

            # Update the version in the project section
            if "project" in toml_content and variable in toml_content["project"]:
                toml_content["project"][variable] = new_version

                with open(file_path, "w", encoding="utf-8") as file:
                    toml.dump(toml_content, file)

                return True
            return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class YamlVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
            return data.get(variable)
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            data[variable] = new_version
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f)
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class JsonVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return data.get(variable)
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data[variable] = new_version
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class XmlVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            element = root.find(variable)
            return element.text if element is not None else None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            element = root.find(variable)
            if element is not None:
                element.text = new_version
                tree.write(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class DockerfileVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        version_pattern = re.compile(
            rf"^\s*ARG\s+{re.escape(variable)}\s*=\s*(.+?)\s*$", re.MULTILINE
        )
        try:
            with open(file_path, "r") as file:
                content = file.read()
            match = version_pattern.search(content)
            return match.group(1) if match else None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        version_pattern = re.compile(
            rf"^\s*(ARG\s+{re.escape(variable)}\s*=\s*)(.+?)\s*$", re.MULTILINE
        )
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            new_content, num_subs = version_pattern.subn(rf"\1{new_version}", content)
            if num_subs > 0:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                return True
            return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class MakefileVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str) -> Optional[str]:
        version_pattern = re.compile(
            rf"^\s*{re.escape(variable)}\s*[:]?=\s*(.+?)\s*$", re.MULTILINE
        )
        try:
            with open(file_path, "r") as file:
                content = file.read()
            match = version_pattern.search(content)
            return match.group(1) if match else None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
        version_pattern = re.compile(
            rf"^\s*({re.escape(variable)}\s*[:]?=\s*)(.+?)\s*$", re.MULTILINE
        )
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            new_content, num_subs = version_pattern.subn(rf"\1{new_version}", content)
            if num_subs > 0:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                return True
            return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


def get_version_handler(file_type: str) -> VersionHandler:
    if file_type == "python":
        logger.info("Python file type detected")
        return PythonVersionHandler()
    elif file_type == "toml":
        logger.info("TOML file type detected")
        return TomlVersionHandler()
    elif file_type == "yaml":
        logger.info("YAML file type detected")
        return YamlVersionHandler()
    elif file_type == "json":
        logger.info("JSON file type detected")
        return JsonVersionHandler()
    elif file_type == "xml":
        logger.info("XML file type detected")
        return XmlVersionHandler()
    elif file_type == "dockerfile":
        logger.info("Dockerfile file type detected")
        return DockerfileVersionHandler()
    elif file_type == "makefile":
        logger.info("Makefile file type detected")
        return MakefileVersionHandler()
    else:
        logger.error(f"Unsupported file type: {file_type}")
        raise ValueError(f"Unsupported file type: {file_type}")


def parse_dot_path(dot_path: str) -> str:
    """
    Converts dot-separated path to a proper file path, if necessary.

    Args:
        dot_path (str): The dot-separated path to the target file.

    Returns:
        str: The corresponding file system path.
    """
    # If the path is pyproject.toml, return it as-is
    if dot_path == "pyproject.toml":
        return dot_path

    # If the path already contains slashes, assume it's a correct file path
    if "/" in dot_path or "\\" in dot_path:
        return dot_path

    # Convert dot-separated path to a file path and add '.py' if necessary
    if "__init__" in dot_path:
        return dot_path.replace(".", os.sep) + ".py"
    else:
        return dot_path.replace(".", os.sep) + ".py"


def parse_version(version: str) -> Optional[tuple]:
    """
    Parses the version to extract the date and count.

    Args:
        version (str): The version string.

    Returns:
        Optional[tuple]: A tuple of (date, count) if successful, otherwise None.
    """
    try:
        date_str, count_str = version.split("-")
        return date_str, int(count_str)
    except ValueError:
        return None


def get_current_date(timezone: str = default_timezone) -> str:
    """Get the current date in a specified timezone.

    This function returns the current date formatted as 'YYYY-MM-DD' in the specified timezone.
    If the specified timezone is not found, it defaults to 'America/New_York'.

    Args:
        timezone (str): The timezone to use. Defaults to 'America/New_York'.

    Returns:
        str: The current date in the specified timezone formatted as 'YYYY-MM-DD'.
    """
    try:
        # Attempt to get the specified timezone
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        # If the timezone is not found, print a message and use the default timezone
        print(f"Unknown timezone '{timezone}'. Using default '{default_timezone}'.")
        tz = ZoneInfo(default_timezone)

    # Get the current date in the specified timezone and format it as 'YYYY-MM-DD'
    return datetime.now(tz).strftime("%Y-%m-%d")


def get_current_datetime_version(timezone: str = default_timezone) -> str:
    """
    Get the current date as a version string.

    Args:
        timezone (str): The timezone to use for generating the version.

    Returns:
        str: A version string based on the current date.
    """
    now = datetime.now()
    return now.strftime("%Y%m%d")


def get_build_version(
    file_config: Dict[str, Any], version_format: str, timezone: str
) -> str:
    """
    Generates the build version based on the current date and the build count.

    Args:
        file_config (Dict[str, Any]): The configuration of the file containing the current version.
        version_format (str): The format to use for the new version.
        timezone (str): The timezone to use for generating the version.

    Returns:
        str: The generated build version.
    """
    # Convert dot-separated path to actual file path if necessary
    file_path = file_config["path"]
    file_type = file_config.get("file_type", "")
    variable = file_config.get("variable", "")

    # Get the current date for versioning
    current_date = get_current_datetime_version(timezone)
    build_count = 1  # Default build count

    try:
        # Use the appropriate handler for reading the version
        handler = get_version_handler(file_type)
        version = handler.read_version(file_path, variable)

        if version:
            # Parse the version to get the last date and count
            parsed_version = parse_version(version)
            if parsed_version:
                last_date, last_count = parsed_version
                if last_date == current_date:
                    build_count = last_count + 1
        else:
            logger.warning(
                f"Could not read version from {file_path}. Starting new versioning."
            )
    except Exception as e:
        logger.error(f"Error reading version from {file_path}: {e}")
        build_count = 1

    # Return the formatted build version
    return version_format.format(current_date=current_date, build_count=build_count)


@click.command()
@click.option("--beta", is_flag=True, help="Use beta versioning")
@click.option("--rc", is_flag=True, help="Use rc versioning")
@click.option("--build", is_flag=True, help="Use build count versioning")
@click.option(
    "--timezone",
    help="Timezone for date calculations (default: value from config or America/New_York)",
)
@click.option(
    "--git-tag/--no-git-tag", default=None, help="Create a Git tag with the new version"
)
@click.option(
    "--auto-commit/--no-auto-commit",
    default=None,
    help="Automatically commit changes when creating a Git tag",
)
def main(
    beta: bool,
    rc: bool,
    build: bool,
    timezone: Optional[str],
    git_tag: Optional[bool],
    auto_commit: Optional[bool],
) -> None:
    """Main function for the bumpcalver CLI tool.

    This function handles the command-line interface for the bumpcalver tool. It loads the configuration,
    determines the new version based on the provided options, updates the version in specified files,
    and optionally creates a Git tag and commits the changes.

    Args:
        beta (bool): Flag to use beta versioning.
        build (bool): Flag to use build count versioning.
        timezone (Optional[str]): Timezone for date calculations.
        git_tag (Optional[bool]): Flag to create a Git tag with the new version.
        auto_commit (Optional[bool]): Flag to automatically commit changes when creating a Git tag.

    Returns:
        None
    """
    # Load the configuration from pyproject.toml
    config: Dict[str, Any] = load_config()
    version_format: str = config.get(
        "version_format", "{current_date}-{build_count:03}"
    )
    file_configs: List[Dict[str, Any]] = config.get("file_configs", [])
    config_timezone: str = config.get("timezone", default_timezone)
    config_git_tag: bool = config.get("git_tag", False)
    config_auto_commit: bool = config.get("auto_commit", False)

    if not file_configs:
        print("No files specified in the configuration.")
        return

    # Use the timezone from the command line if provided; otherwise, use config
    timezone = timezone or config_timezone

    # Determine whether to create a Git tag
    if git_tag is None:
        git_tag = config_git_tag

    # Determine whether to auto-commit changes
    if auto_commit is None:
        auto_commit = config_auto_commit

    # Adjust the base directory
    project_root: str = os.getcwd()
    # Update file paths to be absolute
    for file_config in file_configs:
        file_config["path"] = os.path.join(project_root, file_config["path"])

    try:
        # Get the new version
        if build:
            # Use the first file config for getting the build count
            init_file_config: Dict[str, Any] = file_configs[0]
            new_version: str = get_build_version(
                init_file_config, version_format, timezone
            )
        else:
            new_version = get_current_datetime_version(timezone)

        if beta:
            new_version += "-beta"

        # Update the version in the specified files
        files_updated: List[str] = update_version_in_files(new_version, file_configs)

        # Create a Git tag if enabled
        if git_tag:
            create_git_tag(new_version, files_updated, auto_commit)

        print(f"Updated version to {new_version} in specified files.")
    except (ValueError, KeyError) as e:
        print(f"Error generating version: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
