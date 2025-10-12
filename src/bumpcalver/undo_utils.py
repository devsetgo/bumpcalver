"""
Undo utilities for BumpCalver.

This module provides functionality to undo version bump operations by restoring
files from backups and optionally undoing git operations.

Functions:
    undo_last_operation: Undo the most recent version bump operation.
    undo_operation_by_id: Undo a specific operation by its ID.
    restore_files_from_backups: Restore files from their backup copies.
    undo_git_operations: Undo git commits and tags.

Example:
    success = undo_last_operation()
    if success:
        print("Successfully undid last version bump")
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from .backup_utils import BackupManager


def undo_last_operation(backup_manager: Optional[BackupManager] = None) -> bool:
    """Undo the most recent version bump operation.
    
    Args:
        backup_manager: Optional backup manager instance
        
    Returns:
        True if undo was successful, False otherwise
    """
    if backup_manager is None:
        backup_manager = BackupManager()
    
    latest_operation = backup_manager.get_latest_operation()
    if not latest_operation:
        print("No operations found to undo")
        return False
    
    return undo_operation(latest_operation, backup_manager)


def undo_operation_by_id(operation_id: str, backup_manager: Optional[BackupManager] = None) -> bool:
    """Undo a specific operation by its ID.
    
    Args:
        operation_id: The ID of the operation to undo
        backup_manager: Optional backup manager instance
        
    Returns:
        True if undo was successful, False otherwise
    """
    if backup_manager is None:
        backup_manager = BackupManager()
    
    # Find the operation in history
    history = backup_manager.get_operation_history()
    operation = None
    
    for op in history:
        if op["operation_id"] == operation_id:
            operation = op
            break
    
    if not operation:
        print(f"Operation with ID {operation_id} not found")
        return False
    
    return undo_operation(operation, backup_manager)


def undo_operation(operation: Dict[str, Any], backup_manager: BackupManager) -> bool:
    """Undo a specific operation.
    
    Args:
        operation: The operation record to undo
        backup_manager: Backup manager instance
        
    Returns:
        True if undo was successful, False otherwise
    """
    print(f"Undoing operation: {operation['operation_id']}")
    print(f"Version: {operation['version']}")
    print(f"Timestamp: {operation['timestamp']}")
    
    success = True
    
    # Restore files from backups
    if not restore_files_from_backups(operation["backups"]):
        success = False
    
    # Undo git operations if they were performed
    if operation.get("git_tag") or operation.get("git_commit"):
        if not undo_git_operations(operation):
            success = False
    
    if success:
        print("Successfully undid operation")
    else:
        print("Undo operation completed with some errors")
    
    return success


def restore_files_from_backups(backups: Dict[str, str]) -> bool:
    """Restore files from their backup copies.
    
    Args:
        backups: Dictionary mapping original file paths to backup file paths
        
    Returns:
        True if all files were restored successfully, False otherwise
    """
    if not backups:
        print("No file backups to restore")
        return True
    
    success = True
    
    for original_path, backup_path in backups.items():
        try:
            if not os.path.exists(backup_path):
                print(f"Warning: Backup file {backup_path} not found")
                success = False
                continue
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            
            # Restore the file
            shutil.copy2(backup_path, original_path)
            print(f"Restored {original_path} from backup")
            
        except Exception as e:
            print(f"Failed to restore {original_path}: {e}")
            success = False
    
    return success


def undo_git_operations(operation: Dict[str, Any]) -> bool:
    """Undo git commits and tags.
    
    Args:
        operation: The operation record containing git information
        
    Returns:
        True if git operations were undone successfully, False otherwise
    """
    success = True
    
    try:
        # Check if we're in a git repository
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError:
        print("Not in a git repository, skipping git undo operations")
        return True
    
    # Undo git tag if it was created
    if operation.get("git_tag") and operation.get("git_tag_name"):
        tag_name = operation["git_tag_name"]
        try:
            # Check if tag exists
            result = subprocess.run(
                ["git", "tag", "-l", tag_name],
                capture_output=True,
                text=True
            )
            
            if tag_name in result.stdout.splitlines():
                subprocess.run(["git", "tag", "-d", tag_name], check=True)
                print(f"Deleted git tag: {tag_name}")
            else:
                print(f"Git tag {tag_name} not found, skipping tag deletion")
                
        except subprocess.CalledProcessError as e:
            print(f"Failed to delete git tag {tag_name}: {e}")
            success = False
    
    # Undo git commit if it was created
    if operation.get("git_commit") and operation.get("git_commit_hash"):
        commit_hash = operation["git_commit_hash"]
        try:
            # Get current HEAD commit
            current_head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            # Only reset if the current HEAD is the commit we made
            if current_head == commit_hash:
                subprocess.run(["git", "reset", "--soft", "HEAD~1"], check=True)
                print(f"Reset git commit: {commit_hash[:8]}")
            else:
                print(f"Current HEAD ({current_head[:8]}) is not the expected commit ({commit_hash[:8]})")
                print("Skipping commit reset for safety")
                
        except subprocess.CalledProcessError as e:
            print(f"Failed to reset git commit {commit_hash}: {e}")
            success = False
    
    return success


def list_undo_history(backup_manager: Optional[BackupManager] = None, limit: int = 10) -> None:
    """List recent operations that can be undone.
    
    Args:
        backup_manager: Optional backup manager instance
        limit: Maximum number of operations to display
    """
    if backup_manager is None:
        backup_manager = BackupManager()
    
    history = backup_manager.get_operation_history(limit=limit)
    
    if not history:
        print("No operations found in history")
        return
    
    print(f"Recent operations (showing last {min(len(history), limit)}):")
    print("-" * 80)
    
    for i, operation in enumerate(history, 1):
        timestamp = operation["timestamp"][:19].replace("T", " ")  # Format timestamp
        version = operation["version"]
        operation_id = operation["operation_id"]
        files_count = len(operation["files_updated"])
        git_info = ""
        
        if operation.get("git_tag"):
            git_info += " [TAG]"
        if operation.get("git_commit"):
            git_info += " [COMMIT]"
        
        print(f"{i:2d}. {timestamp} | {version} | {files_count} file(s){git_info}")
        print(f"    ID: {operation_id}")
    
    print("-" * 80)
    print("Use 'bumpcalver --undo' to undo the latest operation")
    print("Use 'bumpcalver --undo-id <operation_id>' to undo a specific operation")


def validate_undo_safety(operation: Dict[str, Any]) -> List[str]:
    """Validate that it's safe to undo an operation.
    
    Args:
        operation: The operation record to validate
        
    Returns:
        List of warning messages, empty if safe to proceed
    """
    warnings = []
    
    # Check if backup files still exist
    for original_path, backup_path in operation["backups"].items():
        if not os.path.exists(backup_path):
            warnings.append(f"Backup file {backup_path} not found")
    
    # Check if original files have been modified since the operation
    for original_path, backup_path in operation["backups"].items():
        if os.path.exists(original_path) and os.path.exists(backup_path):
            try:
                original_mtime = os.path.getmtime(original_path)
                backup_mtime = os.path.getmtime(backup_path)
                
                # If the original file is newer than the backup, it might have been modified
                if original_mtime > backup_mtime + 1:  # 1 second tolerance
                    warnings.append(f"File {original_path} may have been modified since backup")
                    
            except OSError:
                warnings.append(f"Cannot check modification time for {original_path}")
    
    return warnings