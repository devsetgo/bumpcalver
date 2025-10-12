"""
Backup and history utilities for BumpCalver undo functionality.

This module provides functionality to create backups of files before version updates,
store operation history, and manage the undo process. It maintains a history of
version changes to allow users to rollback to previous states.

Functions:
    create_backup: Creates a backup of a file before modification.
    store_operation_history: Stores metadata about a version bump operation.
    get_operation_history: Retrieves the history of version operations.
    cleanup_old_backups: Removes old backup files to prevent disk bloat.

Example:
    backup_info = create_backup("/path/to/file.py")
    store_operation_history("2025.10.12.001", ["file1.py", "file2.py"], git_tag=True)
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class BackupManager:
    """Manages file backups and operation history for undo functionality."""

    def __init__(self, backup_dir: Optional[str] = None, history_file: Optional[str] = None):
        """Initialize the backup manager.

        Args:
            backup_dir: Directory to store backups. If None, uses .bumpcalver/backups
            history_file: Path to history file. If None, uses bumpcalver-history.json in current directory
        """
        if backup_dir is None:
            backup_dir = os.path.join(os.getcwd(), ".bumpcalver", "backups")

        if history_file is None:
            history_file = os.path.join(os.getcwd(), "bumpcalver-history.json")

        self.backup_dir = Path(backup_dir)
        self.history_file = Path(history_file)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of a file before modification.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file, or None if backup failed
        """
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist, skipping backup")
            return None

        try:
            # Create timestamp-based backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            file_name = Path(file_path).name
            backup_filename = f"{timestamp}_{file_name}"
            backup_path = self.backup_dir / backup_filename

            # Copy the file to backup location
            shutil.copy2(file_path, backup_path)
            print(f"Created backup: {backup_path}")

            return str(backup_path)

        except Exception as e:
            print(f"Failed to create backup for {file_path}: {e}")
            return None

    def store_operation_history(
        self,
        operation_id: str,
        version: str,
        files_updated: List[str],
        backups: Dict[str, str],
        git_tag: bool = False,
        git_commit: bool = False,
        git_commit_hash: Optional[str] = None,
        git_tag_name: Optional[str] = None
    ) -> None:
        """Store metadata about a version bump operation.

        Args:
            operation_id: Unique identifier for this operation
            version: The version that was set
            files_updated: List of files that were updated
            backups: Mapping of original file paths to backup file paths
            git_tag: Whether a git tag was created
            git_commit: Whether files were committed to git
            git_commit_hash: Hash of the git commit (if created)
            git_tag_name: Name of the git tag (if created)
        """
        try:
            # Load existing history
            history = self._load_history()

            # Create new operation record
            operation = {
                "operation_id": operation_id,
                "timestamp": datetime.now().isoformat(),
                "version": version,
                "files_updated": files_updated,
                "backups": backups,
                "git_tag": git_tag,
                "git_commit": git_commit,
                "git_commit_hash": git_commit_hash,
                "git_tag_name": git_tag_name
            }

            # Add to history (newest first)
            history.insert(0, operation)

            # Keep only last 50 operations to prevent unbounded growth
            history = history[:50]

            # Save updated history
            self._save_history(history)

        except Exception as e:
            print(f"Failed to store operation history: {e}")

    def get_operation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve the history of version operations.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of operation records, newest first
        """
        try:
            history = self._load_history()
            if limit:
                history = history[:limit]
            return history
        except Exception as e:
            print(f"Failed to load operation history: {e}")
            return []

    def get_latest_operation(self) -> Optional[Dict[str, Any]]:
        """Get the most recent operation.

        Returns:
            The latest operation record, or None if no history exists
        """
        history = self.get_operation_history(limit=1)
        return history[0] if history else None

    def cleanup_old_backups(self, days_to_keep: int = 30) -> None:
        """Remove backup files older than specified days.

        Args:
            days_to_keep: Number of days of backups to retain
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            for backup_file in self.backup_dir.glob("*"):
                if backup_file.name == "history.json":
                    continue

                # Skip if not a file
                if not backup_file.is_file():
                    continue

                # Check file modification time
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    print(f"Removed old backup: {backup_file}")

        except Exception as e:
            print(f"Failed to cleanup old backups: {e}")

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load operation history from JSON file."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save operation history to JSON file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save history: {e}")


def generate_operation_id() -> str:
    """Generate a unique operation ID based on timestamp.

    Returns:
        A unique operation identifier
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def backup_files_before_update(
    file_configs: List[Dict[str, Any]],
    backup_manager: Optional[BackupManager] = None
) -> Tuple[Dict[str, str], BackupManager]:
    """Create backups for all files that will be updated.

    Args:
        file_configs: List of file configurations from bumpcalver config
        backup_manager: Optional existing backup manager instance

    Returns:
        Tuple of (backups dictionary, backup manager instance)
    """
    if backup_manager is None:
        backup_manager = BackupManager()

    backups = {}

    for file_config in file_configs:
        file_path = file_config["path"]
        backup_path = backup_manager.create_backup(file_path)
        if backup_path:
            backups[file_path] = backup_path

    return backups, backup_manager
