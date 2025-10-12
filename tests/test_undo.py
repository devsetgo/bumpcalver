"""
Tests for the undo functionality in BumpCalver.

This module contains comprehensive tests for the backup, history, and undo utilities.
"""

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime
from unittest import mock

from src.bumpcalver.backup_utils import BackupManager, backup_files_before_update, generate_operation_id
from src.bumpcalver.undo_utils import (
    list_undo_history,
    restore_files_from_backups,
    undo_last_operation,
    undo_operation_by_id,
    undo_operation,
    undo_git_operations,
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

    def test_backup_manager_default_paths(self):
        """Test BackupManager with default paths."""
        # Test with None parameters (should use defaults)
        manager = BackupManager(backup_dir=None, history_file=None)

        # Should use current working directory paths
        expected_backup_dir = os.path.join(os.getcwd(), ".bumpcalver", "backups")
        expected_history_file = os.path.join(os.getcwd(), "bumpcalver-history.json")

        self.assertEqual(str(manager.backup_dir), expected_backup_dir)
        self.assertEqual(str(manager.history_file), expected_history_file)

    def test_cleanup_old_backups(self):
        """Test cleanup of old backup files."""
        # Create some backup files with specific timestamps
        old_timestamp = "20200101_120000_000"  # Very old date
        recent_timestamp = "20991231_235959_999"  # Future date

        # Create test files with old and recent timestamps
        old_backup = self.backup_manager.backup_dir / f"{old_timestamp}_old_file.py"
        recent_backup = self.backup_manager.backup_dir / f"{recent_timestamp}_recent_file.py"

        old_backup.touch()
        recent_backup.touch()

        # Set file modification times to match the timestamps
        old_time = datetime(2020, 1, 1, 12, 0, 0).timestamp()
        recent_time = datetime(2099, 12, 31, 23, 59, 59).timestamp()

        os.utime(old_backup, (old_time, old_time))
        os.utime(recent_backup, (recent_time, recent_time))

        # Run cleanup
        self.backup_manager.cleanup_old_backups()

        # Old file should be deleted, recent should remain
        self.assertFalse(old_backup.exists())
        self.assertTrue(recent_backup.exists())

    def test_cleanup_old_backups_exception_handling(self):
        """Test cleanup handles exceptions gracefully."""
        with mock.patch('os.listdir', side_effect=OSError("Permission denied")):
            # Should not raise exception
            self.backup_manager.cleanup_old_backups()

    def test_backup_manager_mkdir_exception(self):
        """Test BackupManager handles directory creation exceptions."""
        with mock.patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            # Should still create the manager, but directory creation might fail
            try:
                BackupManager(backup_dir="/invalid/path/backups")
                # Should not crash
            except OSError:
                pass  # Expected in some cases


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

    def test_backup_files_before_update_with_nonexistent_file(self):
        """Test backup_files_before_update with non-existent file."""
        with isolated_test_environment() as temp_dir:
            temp_backup_dir = os.path.join(temp_dir, "backups")
            backup_manager = BackupManager(backup_dir=temp_backup_dir)

            # Include a non-existent file
            existing_file = create_test_file(temp_dir, "existing.py", "__version__ = '1.0.0'\n")
            nonexistent_file = os.path.join(temp_dir, "nonexistent.py")

            file_configs = [
                {"path": existing_file, "file_type": "python", "variable": "__version__"},
                {"path": nonexistent_file, "file_type": "python", "variable": "__version__"}
            ]

            backups, returned_manager = backup_files_before_update(file_configs, backup_manager)

            # Should only include successful backups (existing file only)
            self.assertIsInstance(backups, dict)
            self.assertEqual(len(backups), 1)  # Only the existing file should be backed up
            self.assertIn(existing_file, backups)
            self.assertNotIn(nonexistent_file, backups)  # Non-existent file should not be in backups

    def test_backup_files_before_update_empty_list(self):
        """Test backup_files_before_update with empty file list."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)
            backups, returned_manager = backup_files_before_update([], backup_manager)
            self.assertEqual(backups, {})
            self.assertIs(returned_manager, backup_manager)

    def test_backup_manager_get_operation_history_file_not_exists(self):
        """Test get_operation_history when history file doesn't exist."""
        with isolated_test_environment() as temp_dir:
            history_file = os.path.join(temp_dir, "nonexistent-history.json")
            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            history = backup_manager.get_operation_history()
            self.assertEqual(history, [])

    def test_backup_manager_get_operation_history_invalid_json(self):
        """Test get_operation_history with invalid JSON file."""
        with isolated_test_environment() as temp_dir:
            history_file = os.path.join(temp_dir, "invalid-history.json")

            # Create invalid JSON file
            with open(history_file, 'w') as f:
                f.write("invalid json content {")

            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            history = backup_manager.get_operation_history()
            self.assertEqual(history, [])

    def test_backup_manager_store_operation_history_exception(self):
        """Test store_operation_history exception handling."""
        with isolated_test_environment() as temp_dir:
            history_file = os.path.join(temp_dir, "history.json")
            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            # Mock json.dump to raise exception
            with mock.patch('json.dump', side_effect=OSError("Permission denied")):
                # Should not raise exception
                backup_manager.store_operation_history(
                    operation_id="test_op",
                    version="1.0.0",
                    files_updated=["test.py"],
                    backups={"test.py": "backup.py"},
                    git_tag=False
                )

    def test_backup_manager_get_latest_operation_empty_history(self):
        """Test get_latest_operation with empty history."""
        with isolated_test_environment() as temp_dir:
            history_file = os.path.join(temp_dir, "empty-history.json")
            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            latest = backup_manager.get_latest_operation()
            self.assertIsNone(latest)

    def test_backup_manager_create_backup_exception(self):
        """Test create_backup exception handling."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Create a file that will cause shutil.copy2 to fail
            source_file = create_test_file(temp_dir, "source.py", "content")

            # Mock shutil.copy2 to raise exception
            with mock.patch('shutil.copy2', side_effect=OSError("Permission denied")):
                result = backup_manager.create_backup(source_file)
                self.assertIsNone(result)

    def test_backup_manager_load_history_exception(self):
        """Test _load_history exception handling."""
        with isolated_test_environment() as temp_dir:
            history_file = os.path.join(temp_dir, "history.json")
            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            # Mock open to raise exception
            with mock.patch('builtins.open', side_effect=OSError("Permission denied")):
                history = backup_manager.get_operation_history()
                self.assertEqual(history, [])

    def test_undo_last_operation_no_history(self):
        """Test undo_last_operation when no history exists."""
        with isolated_test_environment() as temp_dir:
            history_file = os.path.join(temp_dir, "empty-history.json")
            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            result = undo_last_operation(backup_manager)
            self.assertFalse(result)

    def test_undo_git_operations_not_git_repo(self):
        """Test undo_git_operations when not in a git repository."""
        with mock.patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, ['git'])):
            operation = {
                "git_commit": True,
                "git_commit_hash": "abc123",
                "git_tag": True,
                "git_tag_name": "v1.0.0"
            }

            result = undo_git_operations(operation)
            self.assertTrue(result)  # Should return True when not in git repo

    def test_undo_git_operations_commit_hash_mismatch(self):
        """Test undo_git_operations when commit hash doesn't match."""
        def mock_run_side_effect(cmd, **kwargs):
            mock_result = mock.Mock()
            mock_result.returncode = 0

            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                mock_result.stdout = "true\n"
            elif cmd == ["git", "rev-parse", "HEAD"]:
                # Different commit hash
                mock_result.stdout = "different123\n"

            return mock_result

        with mock.patch('subprocess.run', side_effect=mock_run_side_effect):
            operation = {
                "git_commit": True,
                "git_commit_hash": "abc123",
                "git_tag": False
            }

            result = undo_git_operations(operation)
            self.assertTrue(result)  # Should succeed but skip reset

    def test_undo_git_operations_tag_not_found(self):
        """Test undo_git_operations when git tag is not found."""
        def mock_run_side_effect(cmd, **kwargs):
            mock_result = mock.Mock()
            mock_result.returncode = 0

            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                mock_result.stdout = "true\n"
            elif cmd == ["git", "tag", "-l", "v1.0.0"]:
                # Tag not found
                mock_result.stdout = "\n"

            return mock_result

        with mock.patch('subprocess.run', side_effect=mock_run_side_effect):
            operation = {
                "git_commit": False,
                "git_tag": True,
                "git_tag_name": "v1.0.0"
            }

            result = undo_git_operations(operation)
            self.assertTrue(result)  # Should succeed but skip tag deletion
class TestUndoUtilities(unittest.TestCase):
    """Test cases for undo utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_manager = BackupManager(backup_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
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

    def test_undo_operation_by_id_success(self):
        """Test successful undo by operation ID."""
        with isolated_test_environment() as temp_dir:
            # Create test files and backup manager
            history_file = os.path.join(temp_dir, "test-history.json")
            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            # Create original file
            original_file = create_test_file(temp_dir, "test.py", "__version__ = '1.0.0'\n")

            # Create backup
            backup_path = backup_manager.create_backup(original_file)
            self.assertIsNotNone(backup_path)

            # Modify original file
            with open(original_file, 'w') as f:
                f.write("__version__ = '2.0.0'\n")

            # Store operation - ensure backup_path is not None
            if backup_path is not None:
                backup_manager.store_operation_history(
                    operation_id="test_op_123",
                    version="2.0.0",
                    files_updated=[original_file],
                    backups={original_file: backup_path},
                    git_tag=False
                )            # Undo by ID
            result = undo_operation_by_id("test_op_123", backup_manager)
            self.assertTrue(result)

            # Verify file was restored
            with open(original_file, 'r') as f:
                content = f.read()
            self.assertIn("1.0.0", content)

    def test_validate_undo_safety_warnings(self):
        """Test validate_undo_safety with various warning conditions."""
        with isolated_test_environment():
            # Create test operation with missing backup
            operation = {
                "operation_id": "test_op",
                "version": "1.0.0",
                "files_updated": ["test.py"],
                "backups": {"test.py": "/nonexistent/backup.py"},
                "timestamp": "2025-10-12T10:00:00"
            }

            warnings = validate_undo_safety(operation)
            self.assertEqual(len(warnings), 1)
            self.assertIn("Backup file /nonexistent/backup.py not found", warnings[0])

    def test_validate_undo_safety_modified_files(self):
        """Test validate_undo_safety with modified files."""
        with isolated_test_environment() as temp_dir:
            # Create original and backup files
            original_file = create_test_file(temp_dir, "test.py", "__version__ = '1.0.0'\n")
            backup_file = create_test_file(temp_dir, "backup.py", "__version__ = '1.0.0'\n")

            # Make backup file older
            old_time = time.time() - 10  # 10 seconds ago
            os.utime(backup_file, (old_time, old_time))

            operation = {
                "operation_id": "test_op",
                "version": "1.0.0",
                "files_updated": [original_file],
                "backups": {original_file: backup_file},
                "timestamp": "2025-10-12T10:00:00"
            }

            warnings = validate_undo_safety(operation)
            # Should warn about file being potentially modified
            modified_warnings = [w for w in warnings if "may have been modified" in w]
            self.assertEqual(len(modified_warnings), 1)

    def test_validate_undo_safety_os_error(self):
        """Test validate_undo_safety handles OS errors."""
        with isolated_test_environment() as temp_dir:
            original_file = create_test_file(temp_dir, "test.py", "__version__ = '1.0.0'\n")
            backup_file = create_test_file(temp_dir, "backup.py", "__version__ = '1.0.0'\n")

            operation = {
                "operation_id": "test_op",
                "version": "1.0.0",
                "files_updated": [original_file],
                "backups": {original_file: backup_file},
                "timestamp": "2025-10-12T10:00:00"
            }

            with mock.patch('os.path.getmtime', side_effect=OSError("Permission denied")):
                warnings = validate_undo_safety(operation)
                os_error_warnings = [w for w in warnings if "Cannot check modification time" in w]
                self.assertEqual(len(os_error_warnings), 1)

    @mock.patch('subprocess.run')
    def test_undo_git_operations_commit_and_tag(self, mock_run):
        """Test undoing both git commit and tag."""
        # Mock the subprocess calls in order
        def mock_run_side_effect(cmd, **kwargs):
            mock_result = mock.Mock()
            mock_result.returncode = 0

            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                # We're in a git repo
                mock_result.stdout = "true\n"
            elif cmd == ["git", "tag", "-l", "v1.0.0"]:
                # Tag exists
                mock_result.stdout = "v1.0.0\n"
            elif cmd == ["git", "rev-parse", "HEAD"]:
                # Current HEAD matches our commit
                mock_result.stdout = "abc123\n"
            elif cmd == ["git", "tag", "-d", "v1.0.0"]:
                # Tag deletion succeeds
                pass
            elif cmd == ["git", "reset", "--soft", "HEAD~1"]:
                # Commit reset succeeds
                pass

            return mock_result

        mock_run.side_effect = mock_run_side_effect

        operation = {
            "git_commit": True,
            "git_commit_hash": "abc123",
            "git_tag": True,
            "git_tag_name": "v1.0.0"
        }

        result = undo_git_operations(operation)
        self.assertTrue(result)

        # Should call git repo check, tag list check, tag delete, HEAD check, and commit reset
        calls = mock_run.call_args_list
        self.assertEqual(len(calls), 5)

        # Check the calls
        self.assertEqual(calls[0][0][0], ["git", "rev-parse", "--is-inside-work-tree"])
        self.assertEqual(calls[1][0][0], ["git", "tag", "-l", "v1.0.0"])
        self.assertEqual(calls[2][0][0], ["git", "tag", "-d", "v1.0.0"])
        self.assertEqual(calls[3][0][0], ["git", "rev-parse", "HEAD"])
        self.assertEqual(calls[4][0][0], ["git", "reset", "--soft", "HEAD~1"])

    @mock.patch('subprocess.run')
    def test_undo_git_operations_commit_only(self, mock_run):
        """Test undoing only git commit."""
        def mock_run_side_effect(cmd, **kwargs):
            mock_result = mock.Mock()
            mock_result.returncode = 0

            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                # We're in a git repo
                mock_result.stdout = "true\n"
            elif cmd == ["git", "rev-parse", "HEAD"]:
                # Current HEAD matches our commit
                mock_result.stdout = "abc123\n"
            elif cmd == ["git", "reset", "--soft", "HEAD~1"]:
                # Commit reset succeeds
                pass

            return mock_result

        mock_run.side_effect = mock_run_side_effect

        operation = {
            "git_commit": True,
            "git_commit_hash": "abc123",
            "git_tag": False
        }

        result = undo_git_operations(operation)
        self.assertTrue(result)

        # Should call git repo check, HEAD check and commit reset
        calls = mock_run.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][0][0], ["git", "rev-parse", "--is-inside-work-tree"])
        self.assertEqual(calls[1][0][0], ["git", "rev-parse", "HEAD"])
        self.assertEqual(calls[2][0][0], ["git", "reset", "--soft", "HEAD~1"])

    @mock.patch('subprocess.run')
    def test_undo_git_operations_tag_only(self, mock_run):
        """Test undoing only git tag."""
        def mock_run_side_effect(cmd, **kwargs):
            mock_result = mock.Mock()
            mock_result.returncode = 0

            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                # We're in a git repo
                mock_result.stdout = "true\n"
            elif cmd == ["git", "tag", "-l", "v1.0.0"]:
                # Tag exists
                mock_result.stdout = "v1.0.0\n"
            elif cmd == ["git", "tag", "-d", "v1.0.0"]:
                # Tag deletion succeeds
                pass

            return mock_result

        mock_run.side_effect = mock_run_side_effect

        operation = {
            "git_commit": False,
            "git_tag": True,
            "git_tag_name": "v1.0.0"
        }

        result = undo_git_operations(operation)
        self.assertTrue(result)

        # Should call git repo check, tag list check, and tag delete
        calls = mock_run.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][0][0], ["git", "rev-parse", "--is-inside-work-tree"])
        self.assertEqual(calls[1][0][0], ["git", "tag", "-l", "v1.0.0"])
        self.assertEqual(calls[2][0][0], ["git", "tag", "-d", "v1.0.0"])

    @mock.patch('subprocess.run')
    def test_undo_git_operations_failure(self, mock_run):
        """Test handling of git operation failures."""
        def mock_run_side_effect(cmd, **kwargs):
            mock_result = mock.Mock()

            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                # We're in a git repo
                mock_result.returncode = 0
                mock_result.stdout = "true\n"
            elif cmd == ["git", "tag", "-l", "v1.0.0"]:
                # Tag exists
                mock_result.returncode = 0
                mock_result.stdout = "v1.0.0\n"
            elif cmd == ["git", "tag", "-d", "v1.0.0"]:
                # Tag deletion fails
                mock_result.returncode = 1
                raise subprocess.CalledProcessError(1, cmd)

            return mock_result

        mock_run.side_effect = mock_run_side_effect

        operation = {
            "git_commit": False,
            "git_tag": True,
            "git_tag_name": "v1.0.0"
        }

        result = undo_git_operations(operation)
        self.assertFalse(result)

    def test_undo_git_operations_no_git_operations(self):
        """Test when no git operations need to be undone."""
        operation = {
            "git_commit": False,
            "git_tag": False
        }

        result = undo_git_operations(operation)
        self.assertTrue(result)  # Should succeed when nothing to undo

    def test_restore_files_empty_backups(self):
        """Test restore_files_from_backups with empty backups dict."""
        result = restore_files_from_backups({})
        self.assertTrue(result)

    def test_restore_files_backup_not_exists(self):
        """Test restore_files_from_backups with non-existent backup."""
        backups = {
            "original.py": "/nonexistent/backup.py"
        }

        result = restore_files_from_backups(backups)
        self.assertFalse(result)

    def test_restore_files_exception_handling(self):
        """Test restore_files_from_backups exception handling."""
        with isolated_test_environment() as temp_dir:
            backup_file = create_test_file(temp_dir, "backup.py", "content")

            # Mock shutil.copy2 to raise exception
            with mock.patch('shutil.copy2', side_effect=OSError("Permission denied")):
                backups = {
                    "original.py": backup_file
                }

                result = restore_files_from_backups(backups)
                self.assertFalse(result)

    def test_backup_manager_save_history_exception(self):
        """Test _save_history exception handling."""
        with isolated_test_environment() as temp_dir:
            history_file = os.path.join(temp_dir, "history.json")
            backup_manager = BackupManager(backup_dir=temp_dir, history_file=history_file)

            # Mock open to raise IOError to test the print statement (line 225)
            with mock.patch('builtins.open', side_effect=IOError("Permission denied")):
                with mock.patch('builtins.print') as mock_print:
                    backup_manager._save_history([{"test": "data"}])
                    # Verify the error message was printed (line 225)
                    mock_print.assert_called_with("Failed to save history: Permission denied")

    def test_backup_manager_get_operation_history_exception(self):
        """Test get_operation_history exception handling."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Mock _load_history to raise exception
            with mock.patch.object(backup_manager, '_load_history', side_effect=Exception("Test error")):
                history = backup_manager.get_operation_history()
                self.assertEqual(history, [])

    def test_backup_manager_cleanup_not_file(self):
        """Test cleanup_old_backups skipping directories."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Create a subdirectory (not a file)
            subdir = backup_manager.backup_dir / "subdirectory"
            subdir.mkdir()

            # Create a history.json file (should be skipped)
            history_file = backup_manager.backup_dir / "history.json"
            history_file.touch()

            # Should not raise exception and should skip non-files
            backup_manager.cleanup_old_backups()

            # Directory and history.json should still exist
            self.assertTrue(subdir.exists())
            self.assertTrue(history_file.exists())

    def test_backup_manager_cleanup_stat_exception(self):
        """Test cleanup_old_backups handling stat() exceptions."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Create a test file
            test_file = backup_manager.backup_dir / "test_file.py"
            test_file.touch()

            # Mock stat to raise exception
            with mock.patch('pathlib.Path.stat', side_effect=OSError("Permission denied")):
                # Should not raise exception
                backup_manager.cleanup_old_backups()

    def test_backup_manager_store_operation_history_exception(self):
        """Test store_operation_history exception handling."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Mock _save_history to raise exception
            with mock.patch.object(backup_manager, '_save_history', side_effect=Exception("Save error")):
                # Should not raise exception
                backup_manager.store_operation_history(
                    operation_id="test-123",
                    version="1.0.0",
                    files_updated=["test.py"],
                    backups={"test.py": "backup.py"}
                )

    def test_undo_operation_by_id_not_found_coverage(self):
        """Test undo_operation_by_id when operation ID is not found."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Should return False when operation not found
            result = undo_operation_by_id("nonexistent-id", backup_manager)
            self.assertFalse(result)

    def test_restore_files_empty_backups_coverage(self):
        """Test restore_files_from_backups with empty backups dict."""
        result = restore_files_from_backups({})
        self.assertTrue(result)

    def test_list_undo_history_empty_coverage(self):
        """Test list_undo_history with no history."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Should not raise exception
            list_undo_history(backup_manager)

    def test_list_undo_history_with_git_operations_coverage(self):
        """Test list_undo_history formatting with git operations."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Add an operation with git tag and commit
            backup_manager.store_operation_history(
                operation_id="test-123",
                version="1.0.0",
                files_updated=["test.py"],
                backups={"test.py": "backup.py"},
                git_tag=True,
                git_commit=True,
                git_tag_name="v1.0.0",
                git_commit_hash="abc123"
            )

            # Should not raise exception
            list_undo_history(backup_manager)

    def test_undo_last_operation_default_backup_manager(self):
        """Test undo_last_operation with default backup manager."""
        # Test the case where backup_manager is None (line 37 in undo_utils.py)
        result = undo_last_operation()
        self.assertFalse(result)  # Should return False when no operations exist

    def test_undo_operation_by_id_default_backup_manager(self):
        """Test undo_operation_by_id with default backup manager."""
        # Test the case where backup_manager is None (line 58 in undo_utils.py)
        result = undo_operation_by_id("nonexistent")
        self.assertFalse(result)  # Should return False when operation not found

    def test_list_undo_history_default_backup_manager(self):
        """Test list_undo_history with default backup manager."""
        # Test the case where backup_manager is None (line 224 in undo_utils.py)
        list_undo_history()  # Should not raise exception

    def test_backup_files_before_update_default_manager(self):
        """Test backup_files_before_update with default backup manager (line 225)."""
        with isolated_test_environment() as temp_dir:
            # Create a test file
            test_file = create_test_file(temp_dir, "test.py", "content")

            file_configs = [
                {"path": test_file, "file_type": "python"}
            ]

            # Call without backup_manager to trigger line 225
            backups, returned_manager = backup_files_before_update(file_configs)

            self.assertIsInstance(returned_manager, BackupManager)
            self.assertIn(test_file, backups)

    def test_undo_operation_git_failure(self):
        """Test undo_operation when git operations fail."""
        with isolated_test_environment() as temp_dir:
            backup_manager = BackupManager(backup_dir=temp_dir)

            # Create a test file and backup
            test_file = create_test_file(temp_dir, "test.py", "content")
            backup_file = create_test_file(temp_dir, "backup.py", "backup_content")

            operation = {
                "operation_id": "test-123",
                "version": "1.0.0",
                "timestamp": "2025-01-01T00:00:00",
                "files_updated": [test_file],
                "backups": {test_file: backup_file},
                "git_tag": True,
                "git_commit": True,
                "git_tag_name": "v1.0.0",
                "git_commit_hash": "abc123"
            }

            # Mock undo_git_operations to return False (failure)
            with mock.patch('src.bumpcalver.undo_utils.undo_git_operations', return_value=False):
                result = undo_operation(operation, backup_manager)
                # Should return False because git operations failed (line 99)
                self.assertFalse(result)

    def test_undo_git_operations_commit_safety_check(self):
        """Test undo_git_operations safety check for commit reset."""
        def mock_run_side_effect(cmd, **kwargs):
            mock_result = mock.Mock()
            mock_result.returncode = 0

            if cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
                mock_result.stdout = "true\n"
            elif cmd == ["git", "rev-parse", "HEAD"]:
                # Different commit hash (safety check fails) - need full length to trigger
                mock_result.stdout = "different123456789abcdef\n"

            return mock_result

        with mock.patch('subprocess.run', side_effect=mock_run_side_effect):
            with mock.patch('builtins.print') as mock_print:
                operation = {
                    "git_commit": True,
                    "git_tag": False,
                    "git_commit_hash": "abc123456789abcdef0000"
                }

                result = undo_git_operations(operation)
                # Should return True but skip reset for safety (lines 209-211)
                self.assertTrue(result)

                # Verify the safety messages were printed
                mock_print.assert_any_call("Current HEAD (differen) is not the expected commit (abc12345)")
                mock_print.assert_any_call("Skipping commit reset for safety")
if __name__ == '__main__':
    unittest.main()
