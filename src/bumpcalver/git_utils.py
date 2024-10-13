import subprocess
from typing import List


def create_git_tag(version: str, files_to_commit: List[str], auto_commit: bool) -> None:
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
