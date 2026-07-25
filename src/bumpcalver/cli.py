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
from typing import Any, Callable, Dict, List, Optional, Tuple

import click

from . import __version__
from .backup_utils import BackupManager, backup_files_before_update, generate_operation_id
from .config import load_config
from .git_utils import create_git_tag
from .handlers import get_version_handler, update_version_in_files
from .undo_utils import list_undo_history, undo_last_operation, undo_operation_by_id
from .utils import apply_prerelease_suffix, default_timezone, get_build_version, get_current_datetime_version, update_semantic_in_config


def _read_current_version(file_config: Dict[str, Any]) -> Optional[str]:
    """Read a file's current version, returning None if the handler/read fails."""
    try:
        handler = get_version_handler(file_config.get("file_type", ""))
        variable = file_config.get("variable", "")
        extra_kwargs: Dict[str, Any] = {}
        if file_config.get("directive"):
            extra_kwargs["directive"] = file_config["directive"]
        if file_config.get("pattern"):
            extra_kwargs["pattern"] = file_config["pattern"]
        return handler.read_version(file_config["path"], variable, **extra_kwargs)
    except Exception:
        return None


def _apply_semantic_bump(
    bump: Optional[str], major: int, minor: int, patch: int
) -> Tuple[int, int, int]:
    """Increment the requested semver component and persist it to the config file.

    A major bump resets minor/patch to 0; a minor bump resets patch to 0; a
    patch bump only increments patch. Returns the resulting (major, minor, patch).
    """
    if bump == "major":
        major += 1
        minor = 0
        patch = 0
        update_semantic_in_config("major", major)
        update_semantic_in_config("minor", minor)
        update_semantic_in_config("patch", patch)
    elif bump == "minor":
        minor += 1
        patch = 0
        update_semantic_in_config("minor", minor)
        update_semantic_in_config("patch", patch)
    elif bump == "patch":
        patch += 1
        update_semantic_in_config("patch", patch)
    return major, minor, patch


def _compute_new_version(
    *,
    build: bool,
    beta: bool,
    rc: bool,
    release: bool,
    custom: Optional[str],
    file_configs: List[Dict[str, Any]],
    version_format: str,
    timezone: str,
    date_format: str,
    config: Dict[str, Any],
    config_major: int,
    config_minor: int,
    config_patch: int,
    cached_version: Callable[[Dict[str, Any]], Optional[str]],
) -> str:
    """Compute this invocation's new version string.

    Starts from the build-count or plain date/time version, then applies at
    most one of --beta/--rc/--release/--custom. cached_version is used to look
    up the first configured file's current raw version, which pre-release
    suffixing needs to detect and increment an existing suffix count.
    """
    if build:
        print("Build option is set. Calling get_build_version.")
        init_file_config: Dict[str, Any] = file_configs[0]
        new_version: str = get_build_version(
            init_file_config, version_format, timezone, date_format,
            major=config_major, minor=config_minor, patch=config_patch,
        )
    else:
        print("Build option is not set. Calling get_current_datetime_version.")
        new_version = get_current_datetime_version(timezone, date_format)

    if beta or rc or release:
        current_raw_version = cached_version(file_configs[0]) or ""

    if beta:
        new_version = apply_prerelease_suffix(new_version, config.get("beta_format", ".beta"), current_raw_version)
    elif rc:
        new_version = apply_prerelease_suffix(new_version, config.get("rc_format", ".rc"), current_raw_version)
    elif release:
        new_version = apply_prerelease_suffix(new_version, config.get("release_format", ".release"), current_raw_version)
    elif custom:
        new_version += f".{custom}"

    return new_version


def _files_that_would_change(
    file_configs: List[Dict[str, Any]],
    new_version: str,
    cached_version: Callable[[Dict[str, Any]], Optional[str]],
) -> List[str]:
    """Return the paths of files whose current version differs from new_version.

    Shared by the no-op guard (empty list => nothing to do) and --dry-run
    (prints this list instead of writing anything).
    """
    return [
        file_config["path"]
        for file_config in file_configs
        if cached_version(file_config) != new_version
    ]


def _all_files_already_updated(
    file_configs: List[Dict[str, Any]],
    new_version: str,
    cached_version: Callable[[Dict[str, Any]], Optional[str]],
) -> bool:
    """True if every configured file already contains new_version (i.e. this bump is a no-op)."""
    return not _files_that_would_change(file_configs, new_version, cached_version)


def _create_git_tag_and_commit(
    new_version: str, files_updated: List[str], git_tag: bool, auto_commit: bool
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git tag (and, if requested, a commit) for the new version.

    Returns (git_commit_hash, git_tag_name); both are None if git_tag is False
    or the underlying git command(s) failed (git operations are best-effort and
    never fail the overall version bump).
    """
    if not git_tag:
        return None, None

    git_commit_hash = None
    git_tag_name = None
    try:
        if auto_commit:
            # create_git_tag() creates the commit itself, so the hash can only
            # be read back afterward.
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
        pass

    return git_commit_hash, git_tag_name


@click.command()
@click.version_option(__version__, "--version", "-V")
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
@click.option(
    "--bump",
    type=click.Choice(["major", "minor", "patch"]),
    default=None,
    help="Increment the specified semantic version component in config",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would change without writing any files or creating a git tag/commit",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, dir_okay=False),
    envvar="BUMPCALVER_CONFIG",
    help="Path to a pyproject.toml/bumpcalver.toml to use instead of auto-discovery "
    "in the current directory (env var: BUMPCALVER_CONFIG). File paths inside it are "
    "resolved relative to the config file's own directory, not the current directory.",
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
    undo: bool,
    undo_id: Optional[str],
    list_history: bool,
    bump: Optional[str],
    dry_run: bool,
    config_file: Optional[str],
) -> None:
    """Bump this project's version and write it to every configured file.

    Reads `[tool.bumpcalver]` from `pyproject.toml` (or `bumpcalver.toml`) for
    the file list and defaults; CLI flags override config values where both
    exist. At most one of `--beta`/`--rc`/`--release`/`--custom` may be set.
    Optionally creates a git tag and/or commit — or preview with `--dry-run`
    instead of writing anything. Undo a previous run with `--undo`,
    `--undo-id`, or `--list-history` (mutually exclusive with every
    version-bump option, including `--dry-run`).
    """
    # Check for conflicting undo options with version bump options FIRST
    version_bump_options = [beta, rc, release, build, bool(custom), bool(bump)]
    undo_options = [undo, bool(undo_id), list_history]

    if any(version_bump_options) and any(undo_options):
        raise click.UsageError(
            "Undo options (--undo, --undo-id, --list-history) cannot be used with version bump options."
        )

    if dry_run and any(undo_options):
        raise click.UsageError(
            "--dry-run cannot be used with --undo, --undo-id, or --list-history."
        )

    if config_file and any(undo_options):
        # Undo operations locate their history purely via os.getcwd() (see
        # undo_utils.py) and don't accept a project root override, so
        # --config-file would be silently ignored here rather than doing
        # what its name implies — reject explicitly instead of guessing.
        raise click.UsageError(
            "--config-file cannot be used with --undo, --undo-id, or --list-history."
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

    config: Dict[str, Any] = load_config(config_file)
    version_format: str = config.get(
        "version_format", "{current_date}-{build_count:03}"
    )
    date_format: str = config.get("date_format", "%Y.%m.%d")
    file_configs: List[Dict[str, Any]] = config.get("file_configs", [])
    config_timezone: str = config.get("timezone", default_timezone)
    config_git_tag: bool = config.get("git_tag", False)
    config_auto_commit: bool = config.get("auto_commit", False)
    config_major: int = config.get("major", 0)
    config_minor: int = config.get("minor", 0)
    config_patch: int = config.get("patch", 0)

    config_major, config_minor, config_patch = _apply_semantic_bump(
        bump, config_major, config_minor, config_patch
    )

    if not file_configs:  # pragma: no cover
        print("No files specified in the configuration.")
        return

    timezone = timezone or config_timezone
    if git_tag is None:
        git_tag = config_git_tag
    if auto_commit is None:
        auto_commit = config_auto_commit

    # File paths in the config are relative to wherever the config file
    # lives, not necessarily the CLI's cwd — that's the whole point of
    # --config-file letting you invoke bumpcalver from a different directory.
    if config_file:
        project_root: str = os.path.dirname(os.path.abspath(config_file))
    else:
        project_root = os.getcwd()
    for file_config in file_configs:
        file_config["path"] = os.path.join(project_root, file_config["path"])

    # Cache each file's current version per (path, variable, directive) so it's read
    # at most once per invocation, even though it's needed both for the pre-release
    # suffix lookup and the no-op guard below. Keyed on the triple (not just path)
    # because a single file can have multiple configured entries with different
    # variables/directives (e.g. a Dockerfile with separate ARG and ENV entries).
    _version_cache: Dict[tuple, Optional[str]] = {}

    def _cached_current_version(file_config: Dict[str, Any]) -> Optional[str]:
        key = (file_config["path"], file_config.get("variable", ""), file_config.get("directive", ""))
        if key not in _version_cache:
            _version_cache[key] = _read_current_version(file_config)
        return _version_cache[key]

    try:
        new_version = _compute_new_version(
            build=build,
            beta=beta,
            rc=rc,
            release=release,
            custom=custom,
            file_configs=file_configs,
            version_format=version_format,
            timezone=timezone,
            date_format=date_format,
            config=config,
            config_major=config_major,
            config_minor=config_minor,
            config_patch=config_patch,
            cached_version=_cached_current_version,
        )

        files_that_would_change = _files_that_would_change(
            file_configs, new_version, _cached_current_version
        )

        if dry_run:
            if not files_that_would_change:
                print(f"[dry-run] Version already set to {new_version}; no files would be updated.")
            else:
                print(f"[dry-run] Would bump version to {new_version} in:")
                for path in files_that_would_change:
                    print(f"[dry-run]   {path}")
                if git_tag:
                    action = "commit and create" if auto_commit else "create"
                    print(f"[dry-run] Would {action} git tag '{new_version}'")
            return

        # No-op guard: if all configured files already contain the computed version,
        # do not create backups, write undo history, or attempt git operations.
        if not files_that_would_change:
            print(f"Version already set to {new_version}; no files to update.")
            return

        # Create backup manager and backup files before making changes. Rooted
        # at project_root (not necessarily os.getcwd()) so that with
        # --config-file, undo history/backups stay colocated with the actual
        # project being versioned rather than wherever the CLI was invoked
        # from — otherwise `--undo` run later from the project's own
        # directory would never find them.
        backup_manager = BackupManager(
            backup_dir=os.path.join(project_root, ".bumpcalver", "backups"),
            history_file=os.path.join(project_root, "bumpcalver-history.json"),
        )
        operation_id = generate_operation_id()
        backups, _ = backup_files_before_update(file_configs, backup_manager)

        print(f"Calling update_version_in_files with version: {new_version}")
        files_updated: List[str] = update_version_in_files(new_version, file_configs)
        print(f"Files updated: {files_updated}")

        if not files_updated:
            # Nothing was changed; avoid creating undo history entries for a no-op.
            # Clean up any backups we created since there is nothing to undo.
            for backup_path in backups.values():
                try:
                    if backup_path and os.path.exists(backup_path):
                        os.remove(backup_path)
                except Exception:
                    pass

            print(f"No files were updated; version already set to {new_version}.")
            return

        # Handle git operations and capture information for undo
        git_commit_hash, git_tag_name = _create_git_tag_and_commit(
            new_version, files_updated, git_tag, auto_commit
        )

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
