"""
Git utilities for BumpCalver.

This module provides utility functions for performing Git operations such as creating tags
and committing changes. It is used by the BumpCalver CLI to automate version control tasks.

Functions:
    create_git_tag: Creates a Git tag and optionally commits changes.

Example:
    To create a Git tag and commit changes:
        create_git_tag("v1.0.0", ["file1.py", "file2.py"], auto_commit=True)
"""

import subprocess
from typing import List


def create_git_tag(version: str, files_to_commit: List[str], auto_commit: bool) -> None:
    """
    Creates a Git tag and optionally commits changes.

    This function checks if the specified Git tag already exists. If it does not,
    it creates the tag. If auto-commit is enabled, it stages the specified files
    and commits them before creating the tag.

    Args:
        version (str): The version string to use as the Git tag.
        files_to_commit (List[str]): A list of file paths to commit if auto-commit is enabled.
        auto_commit (bool): Whether to automatically commit changes before creating the tag.

    Raises:
        subprocess.CalledProcessError: If there is an error during Git operations.

    Example:
        To create a Git tag and commit changes:
            create_git_tag("v1.0.0", ["file1.py", "file2.py"], auto_commit=True)
    """
    try:
        # Check if in a Git repository first
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
        )

        # Check if the Git tag already exists
        tag_check = subprocess.run(
            ["git", "tag", "-l", version], capture_output=True, text=True
        )
        if version in tag_check.stdout.splitlines():
            print(f"Tag '{version}' already exists. Skipping tag creation.")
            return

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
