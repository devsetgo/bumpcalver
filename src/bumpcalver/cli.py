"""
BumpCalver CLI.

This module provides a command-line interface for BumpCalver, a tool for calendar-based version bumping.
It allows users to update version strings in their project's files based on the current date and build count.
Additionally, it can create Git tags and commit changes automatically. The CLI also supports undoing
version bump operations to restore previous states.

Functions:
    main: The main entry point for the CLI.

Example:
    To bump the version using the current date and build count:
        $ bumpcalver --build

    To create a beta version:
        $ bumpcalver --build --beta

    To use a specific timezone:
        $ bumpcalver --build --timezone Europe/London

    To bump the version, commit changes, and create a Git tag:
        $ bumpcalver --build --git-tag --auto-commit

    To undo the last version bump:
        $ bumpcalver --undo

    To list recent operations:
        $ bumpcalver --list-history

    To undo a specific operation:
        $ bumpcalver --undo-id <operation_id>
"""

import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

import click

from .backup_utils import BackupManager, backup_files_before_update, generate_operation_id
from .config import load_config
from .git_utils import create_git_tag
from .handlers import update_version_in_files
from .undo_utils import list_undo_history, undo_last_operation, undo_operation_by_id
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
@click.option("--undo", is_flag=True, help="Undo the last version bump operation")
@click.option("--undo-id", default=None, help="Undo a specific operation by ID")
@click.option("--list-history", is_flag=True, help="List recent operations that can be undone")
def main(
    beta: bool,
    rc: bool,
    build: bool,
    release: bool,
    custom: str,
    timezone: Optional[str],
    git_tag: Optional[bool],
    auto_commit: Optional[bool],
    undo: bool,
    undo_id: Optional[str],
    list_history: bool,
) -> None:
    # Check for conflicting undo options with version bump options FIRST
    version_bump_options = [beta, rc, release, build, bool(custom)]
    undo_options = [undo, bool(undo_id), list_history]

    if any(version_bump_options) and any(undo_options):
        raise click.UsageError(
            "Undo options (--undo, --undo-id, --list-history) cannot be used with version bump options."
        )

    # Handle undo and history commands
    if list_history:
        list_undo_history()
        return

    if undo:
        success = undo_last_operation()
        sys.exit(0 if success else 1)

    if undo_id:
        success = undo_operation_by_id(undo_id)
        sys.exit(0 if success else 1)

    # Original version bump logic
    selected_options = [beta, rc, release]
    if custom:
        selected_options.append(True)

    if sum(bool(option) for option in selected_options) > 1:
        raise click.UsageError(
            "Only one of --beta, --rc, --release, or --custom can be set at a time."
        )

    config: Dict[str, Any] = load_config()
    version_format: str = config.get(
        "version_format", "{current_date}-{build_count:03}"
    )
    date_format: str = config.get("date_format", "%Y.%m.%d")
    file_configs: List[Dict[str, Any]] = config.get("file_configs", [])
    config_timezone: str = config.get("timezone", default_timezone)
    config_git_tag: bool = config.get("git_tag", False)
    config_auto_commit: bool = config.get("auto_commit", False)

    if not file_configs:  # pragma: no cover
        print("No files specified in the configuration.")
        return

    timezone = timezone or config_timezone
    if git_tag is None:
        git_tag = config_git_tag
    if auto_commit is None:
        auto_commit = config_auto_commit

    project_root: str = os.getcwd()
    for file_config in file_configs:
        file_config["path"] = os.path.join(project_root, file_config["path"])

    try:
        # Create backup manager and backup files before making changes
        backup_manager = BackupManager()
        operation_id = generate_operation_id()
        backups, _ = backup_files_before_update(file_configs, backup_manager)

        if build:
            print("Build option is set. Calling get_build_version.")
            init_file_config: Dict[str, Any] = file_configs[0]
            new_version: str = get_build_version(
                init_file_config, version_format, timezone, date_format
            )
        else:
            print("Build option is not set. Calling get_current_datetime_version.")
            new_version = get_current_datetime_version(timezone, date_format)

        if beta:
            new_version += ".beta"
        elif rc:
            new_version += ".rc"
        elif release:
            new_version += ".release"
        elif custom:
            new_version += f".{custom}"

        print(f"Calling update_version_in_files with version: {new_version}")
        files_updated: List[str] = update_version_in_files(new_version, file_configs)
        print(f"Files updated: {files_updated}")

        # Handle git operations and capture information for undo
        git_commit_hash = None
        git_tag_name = None

        if git_tag:
            # Get current commit hash before creating tag
            try:
                if auto_commit:
                    # The create_git_tag function will create a commit, so we need to get the hash afterwards
                    create_git_tag(new_version, files_updated, auto_commit)
                    git_commit_hash = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=True
                    ).stdout.strip()
                else:
                    create_git_tag(new_version, files_updated, auto_commit)

                git_tag_name = new_version

            except subprocess.CalledProcessError:
                # Git operations failed, but don't fail the whole operation
                pass

        # Store operation history for undo functionality
        backup_manager.store_operation_history(
            operation_id=operation_id,
            version=new_version,
            files_updated=files_updated,
            backups=backups,
            git_tag=git_tag,
            git_commit=git_tag and auto_commit,
            git_commit_hash=git_commit_hash,
            git_tag_name=git_tag_name
        )

        print(f"Updated version to {new_version} in specified files.")
        print(f"Operation ID: {operation_id} (use 'bumpcalver --undo' to undo)")

    except (ValueError, KeyError) as e:
        print(f"Error generating version: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
