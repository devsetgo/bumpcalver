"""
Tests for the undo functionality in BumpCalver.

This module contains comprehensive tests for the backup, history, and undo utilities.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from src.bumpcalver.backup_utils import BackupManager, backup_files_before_update, generate_operation_id
from src.bumpcalver.undo_utils import (
    list_undo_history,
    restore_files_from_backups,
    undo_last_operation,
    undo_operation_by_id,
    validate_undo_safety
)
from tests.test_utils_isolated import isolated_test_environment, create_test_file


class TestBackupManager(unittest.TestCase):
    """Test cases for BackupManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_manager = BackupManager(backup_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_backup_success(self):
        """Test successful file backup creation."""
        with isolated_test_environment() as test_dir:
            # Create a test file
            test_file = create_test_file(test_dir, "test.py", "__version__ = '1.0.0'\n")
            
            # Create backup
            backup_path = self.backup_manager.create_backup(test_file)
            
            # Verify backup was created
            self.assertIsNotNone(backup_path)
            if backup_path is not None:  # Type guard
                self.assertTrue(os.path.exists(backup_path))
                
                # Verify backup content matches original
                with open(backup_path, 'r') as f:
                    content = f.read()
                self.assertIn("__version__ = '1.0.0'", content)

    def test_create_backup_nonexistent_file(self):
        """Test backup creation for non-existent file."""
        backup_path = self.backup_manager.create_backup("/nonexistent/file.py")
        self.assertIsNone(backup_path)

    def test_store_and_retrieve_operation_history(self):
        """Test storing and retrieving operation history."""
        # Start with a clean backup manager
        operation_id = "test_op_001"
        version = "2025.10.12.001"
        files_updated = ["file1.py", "file2.py"]
        backups = {"file1.py": "backup1.py", "file2.py": "backup2.py"}
        
        # Store operation
        self.backup_manager.store_operation_history(
            operation_id=operation_id,
            version=version,
            files_updated=files_updated,
            backups=backups,
            git_tag=True,
            git_commit=True,
            git_commit_hash="abc123",
            git_tag_name="v2025.10.12.001"
        )
        
        # Retrieve history
        history = self.backup_manager.get_operation_history()
        
        # Find our operation (it might not be the only one)
        our_operation = None
        for op in history:
            if op["operation_id"] == operation_id:
                our_operation = op
                break
        
        self.assertIsNotNone(our_operation, "Our operation should be found in history")
        if our_operation is not None:  # Type guard
            self.assertEqual(our_operation["operation_id"], operation_id)
            self.assertEqual(our_operation["version"], version)
            self.assertEqual(our_operation["files_updated"], files_updated)
            self.assertEqual(our_operation["backups"], backups)
            self.assertTrue(our_operation["git_tag"])
            self.assertTrue(our_operation["git_commit"])
            self.assertEqual(our_operation["git_commit_hash"], "abc123")
            self.assertEqual(our_operation["git_tag_name"], "v2025.10.12.001")

    def test_get_latest_operation(self):
        """Test retrieving the latest operation."""
        # Store multiple operations
        for i in range(3):
            self.backup_manager.store_operation_history(
                operation_id=f"op_{i}",
                version=f"2025.10.12.{i:03d}",
                files_updated=[f"file{i}.py"],
                backups={f"file{i}.py": f"backup{i}.py"}
            )
        
        # Get latest operation
        latest = self.backup_manager.get_latest_operation()
        
        self.assertIsNotNone(latest)
        if latest is not None:  # Type guard
            self.assertEqual(latest["operation_id"], "op_2")  # Latest should be the last one added

    def test_history_limit(self):
        """Test that history is limited to prevent unbounded growth."""
        # Store more than the limit (50 operations)
        for i in range(55):
            self.backup_manager.store_operation_history(
                operation_id=f"op_{i}",
                version=f"2025.10.12.{i:03d}",
                files_updated=[f"file{i}.py"],
                backups={f"file{i}.py": f"backup{i}.py"}
            )
        
        # Verify history is limited
        history = self.backup_manager.get_operation_history()
        self.assertEqual(len(history), 50)
        
        # Verify newest operations are kept
        self.assertEqual(history[0]["operation_id"], "op_54")
        self.assertEqual(history[-1]["operation_id"], "op_5")


class TestBackupUtilities(unittest.TestCase):
    """Test cases for backup utility functions."""

    def test_generate_operation_id(self):
        """Test operation ID generation."""
        import time
        
        op_id1 = generate_operation_id()
        time.sleep(0.001)  # Small delay to ensure different timestamps
        op_id2 = generate_operation_id()
        
        # Should be different and contain timestamp elements
        self.assertNotEqual(op_id1, op_id2)
        self.assertTrue(len(op_id1) > 10)  # Should be reasonably long
        self.assertTrue("_" in op_id1)  # Should contain separators

    def test_backup_files_before_update(self):
        """Test backing up multiple files before update."""
        with isolated_test_environment() as test_dir:
            temp_backup_dir = os.path.join(test_dir, "backups")
            backup_manager = BackupManager(backup_dir=temp_backup_dir)
            
            # Create test files
            file1 = create_test_file(test_dir, "file1.py", "__version__ = '1.0.0'\n")
            file2 = create_test_file(test_dir, "file2.toml", 'version = "1.0.0"\n')
            
            file_configs = [
                {"path": file1, "file_type": "python", "variable": "__version__"},
                {"path": file2, "file_type": "toml", "variable": "version"}
            ]
            
            # Create backups
            backups, returned_manager = backup_files_before_update(file_configs, backup_manager)
            
            # Verify backups were created
            self.assertEqual(len(backups), 2)
            self.assertIn(file1, backups)
            self.assertIn(file2, backups)
            self.assertIs(returned_manager, backup_manager)
            
            # Verify backup files exist
            for backup_path in backups.values():
                self.assertTrue(os.path.exists(backup_path))


class TestUndoUtilities(unittest.TestCase):
    """Test cases for undo utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_manager = BackupManager(backup_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_restore_files_from_backups(self):
        """Test restoring files from backups."""
        with isolated_test_environment() as test_dir:
            # Create original file
            original_file = create_test_file(test_dir, "test.py", "__version__ = '1.0.0'\n")
            
            # Create backup
            backup_path = self.backup_manager.create_backup(original_file)
            self.assertIsNotNone(backup_path)
            
            if backup_path is not None:  # Type guard
                # Modify original file
                with open(original_file, 'w') as f:
                    f.write("__version__ = '2.0.0'\n")
                
                # Restore from backup
                backups = {original_file: backup_path}
                success = restore_files_from_backups(backups)
                
                # Verify restoration
                self.assertTrue(success)
                with open(original_file, 'r') as f:
                    content = f.read()
                self.assertIn("__version__ = '1.0.0'", content)

    def test_restore_files_missing_backup(self):
        """Test restoring files when backup is missing."""
        with isolated_test_environment() as test_dir:
            original_file = create_test_file(test_dir, "test.py", "__version__ = '1.0.0'\n")
            missing_backup = os.path.join(test_dir, "missing_backup.py")
            
            backups = {original_file: missing_backup}
            success = restore_files_from_backups(backups)
            
            self.assertFalse(success)

    def test_validate_undo_safety(self):
        """Test undo safety validation."""
        with isolated_test_environment() as test_dir:
            # Create test file and backup
            original_file = create_test_file(test_dir, "test.py", "__version__ = '1.0.0'\n")
            backup_path = self.backup_manager.create_backup(original_file)
            
            operation = {
                "operation_id": "test_op",
                "backups": {original_file: backup_path}
            }
            
            # Test with valid backup
            warnings = validate_undo_safety(operation)
            self.assertEqual(len(warnings), 0)
            
            # Test with missing backup
            operation["backups"] = {original_file: "/nonexistent/backup.py"}
            warnings = validate_undo_safety(operation)
            self.assertGreater(len(warnings), 0)
            self.assertTrue(any("not found" in warning for warning in warnings))

    @mock.patch('src.bumpcalver.undo_utils.restore_files_from_backups')
    @mock.patch('src.bumpcalver.undo_utils.undo_git_operations')
    def test_undo_last_operation(self, mock_undo_git, mock_restore_files):
        """Test undoing the last operation."""
        # Set up mock returns
        mock_restore_files.return_value = True
        mock_undo_git.return_value = True
        
        # Store an operation
        self.backup_manager.store_operation_history(
            operation_id="test_op",
            version="2025.10.12.001",
            files_updated=["test.py"],
            backups={"test.py": "backup.py"},
            git_tag=True
        )
        
        # Test undo
        success = undo_last_operation(self.backup_manager)
        
        self.assertTrue(success)
        mock_restore_files.assert_called_once()
        mock_undo_git.assert_called_once()

    def test_undo_operation_by_id_not_found(self):
        """Test undoing operation with non-existent ID."""
        success = undo_operation_by_id("nonexistent_id", self.backup_manager)
        self.assertFalse(success)

    @mock.patch('subprocess.run')
    def test_undo_git_operations_tag_deletion(self, mock_run):
        """Test undoing git tag operations."""
        from src.bumpcalver.undo_utils import undo_git_operations
        
        # Mock git commands
        mock_run.side_effect = [
            # git rev-parse --is-inside-work-tree
            mock.Mock(returncode=0),
            # git tag -l <tag_name>
            mock.Mock(stdout="v1.0.0\n", returncode=0),
            # git tag -d <tag_name>
            mock.Mock(returncode=0)
        ]
        
        operation = {
            "git_tag": True,
            "git_tag_name": "v1.0.0",
            "git_commit": False
        }
        
        success = undo_git_operations(operation)
        self.assertTrue(success)
        
        # Verify git commands were called
        self.assertEqual(mock_run.call_count, 3)

    @mock.patch('builtins.print')
    def test_list_undo_history_empty(self, mock_print):
        """Test listing undo history when empty."""
        # Create a fresh backup manager with empty directory and history file
        import tempfile
        temp_dir = tempfile.mkdtemp()
        history_file = os.path.join(temp_dir, "test-history.json")
        empty_backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)
        
        list_undo_history(empty_backup_manager)
        
        # Should print message about no operations
        mock_print.assert_any_call("No operations found in history")

    @mock.patch('builtins.print')
    def test_list_undo_history_with_operations(self, mock_print):
        """Test listing undo history with operations."""
        # Create a fresh backup manager with isolated history file
        import tempfile
        temp_dir = tempfile.mkdtemp()
        history_file = os.path.join(temp_dir, "test-history.json")
        test_backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)
        
        # Store some operations
        for i in range(3):
            test_backup_manager.store_operation_history(
                operation_id=f"op_{i}",
                version=f"2025.10.12.{i:03d}",
                files_updated=[f"file{i}.py"],
                backups={f"file{i}.py": f"backup{i}.py"},
                git_tag=(i % 2 == 0)  # Alternate git tag
            )
        
        list_undo_history(test_backup_manager, limit=5)
        
        # Should print operation details
        mock_print.assert_any_call("Recent operations (showing last 3):")


if __name__ == '__main__':
    unittest.main()