import os
import sys
from typing import Any, Dict, List, Optional

import click

from .config import load_config
from .git_utils import create_git_tag
from .handlers import update_version_in_files
from .utils import default_timezone, get_build_version, get_current_datetime_version


@click.command()
@click.option("--beta", is_flag=True, help="Add -beta to version")
@click.option("--rc", is_flag=True, help="Add -rc to version")
@click.option("--release", is_flag=True, help="Add -release to version")
@click.option("--custom", default=None, help="Add -<WhatEverYouWant> to version")
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
    release: bool,
    custom: str,
    timezone: Optional[str],
    git_tag: Optional[bool],
    auto_commit: Optional[bool],
) -> None:
    """ """
    # Check for mutually exclusive options
    selected_options = [beta, rc, release]
    if custom:
        selected_options.append(True)

    if sum(bool(option) for option in selected_options) > 1:
        raise click.UsageError(
            "Only one of --beta, --rc, --release, or --custom can be set at a time."
        )

    # Load the configuration from pyproject.toml
    config: Dict[str, Any] = load_config()
    version_format: str = config.get(
        "version_format", "{current_date}-{build_count:03}"
    )
    file_configs: List[Dict[str, Any]] = config.get("file_configs", [])
    config_timezone: str = config.get("timezone", default_timezone)
    config_git_tag: bool = config.get("git_tag", False)
    config_auto_commit: bool = config.get("auto_commit", False)

    if not file_configs:  # pragma: no cover
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
            new_version += ".beta"
        elif rc:
            new_version += ".rc"
        elif release:
            new_version += ".release"
        elif custom:
            new_version += f".{custom}"

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
