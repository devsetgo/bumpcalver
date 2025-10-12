"""
Tests for CLI undo functionality in BumpCalver.

This module contains tests for the new undo-related CLI options.
"""

from unittest import mock
from click.testing import CliRunner

from src.bumpcalver.cli import main


class TestCliUndo:
    """Test cases for CLI undo functionality."""

    @mock.patch('src.bumpcalver.cli.list_undo_history')
    def test_list_history_option(self, mock_list_history):
        """Test the --list-history CLI option."""
        runner = CliRunner()
        result = runner.invoke(main, ["--list-history"])

        assert result.exit_code == 0
        mock_list_history.assert_called_once()

    @mock.patch('src.bumpcalver.cli.undo_last_operation')
    def test_undo_option_success(self, mock_undo_last):
        """Test successful --undo CLI option."""
        mock_undo_last.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["--undo"])

        assert result.exit_code == 0
        mock_undo_last.assert_called_once()

    @mock.patch('src.bumpcalver.cli.undo_last_operation')
    def test_undo_option_failure(self, mock_undo_last):
        """Test failed --undo CLI option."""
        mock_undo_last.return_value = False

        runner = CliRunner()
        result = runner.invoke(main, ["--undo"])

        assert result.exit_code == 1
        mock_undo_last.assert_called_once()

    @mock.patch('src.bumpcalver.cli.undo_operation_by_id')
    def test_undo_id_option_success(self, mock_undo_by_id):
        """Test successful --undo-id CLI option."""
        mock_undo_by_id.return_value = True

        runner = CliRunner()
        result = runner.invoke(main, ["--undo-id", "test_operation_123"])

        assert result.exit_code == 0
        mock_undo_by_id.assert_called_once_with("test_operation_123")

    @mock.patch('src.bumpcalver.cli.undo_operation_by_id')
    def test_undo_id_option_failure(self, mock_undo_by_id):
        """Test failed --undo-id CLI option."""
        mock_undo_by_id.return_value = False

        runner = CliRunner()
        result = runner.invoke(main, ["--undo-id", "nonexistent_operation"])

        assert result.exit_code == 1
        mock_undo_by_id.assert_called_once_with("nonexistent_operation")

    def test_undo_conflicts_with_version_options(self):
        """Test that undo options conflict with version bump options."""
        runner = CliRunner()

        # Test --undo with --build
        result = runner.invoke(main, ["--undo", "--build"])
        assert result.exit_code != 0
        assert "Undo options" in result.output
        assert "cannot be used with version bump options" in result.output

        # Test --undo-id with --beta
        result = runner.invoke(main, ["--undo-id", "test", "--beta"])
        assert result.exit_code != 0
        assert "Undo options" in result.output

        # Test --list-history with --rc
        result = runner.invoke(main, ["--list-history", "--rc"])
        assert result.exit_code != 0
        assert "Undo options" in result.output

    def test_multiple_undo_options_allowed(self):
        """Test that multiple undo options can work together (should not conflict)."""
        # Note: The current implementation would process them in order,
        # so --list-history would execute and return before --undo is processed
        runner = CliRunner()

        with mock.patch('src.bumpcalver.cli.list_undo_history') as mock_list:
            result = runner.invoke(main, ["--list-history", "--undo"])
            assert result.exit_code == 0
            mock_list.assert_called_once()


class TestUndoIntegration:
    """Integration tests for undo functionality."""

    @mock.patch('src.bumpcalver.cli.BackupManager')
    @mock.patch('src.bumpcalver.cli.backup_files_before_update')
    @mock.patch('src.bumpcalver.cli.load_config')
    @mock.patch('src.bumpcalver.cli.update_version_in_files')
    @mock.patch('src.bumpcalver.cli.get_current_datetime_version')
    def test_version_bump_creates_backup_and_history(
        self,
        mock_get_version,
        mock_update_files,
        mock_load_config,
        mock_backup_files,
        mock_backup_manager_class
    ):
        """Test that version bump operations create backups and history."""
        # Setup mocks
        mock_backup_manager = mock.Mock()
        mock_backup_manager_class.return_value = mock_backup_manager

        mock_load_config.return_value = {
            "version_format": "{current_date}",
            "date_format": "%Y.%m.%d",
            "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
            "timezone": "UTC",
            "git_tag": False,
            "auto_commit": False,
        }

        mock_get_version.return_value = "2025.10.12"
        mock_update_files.return_value = ["test.py"]
        mock_backup_files.return_value = ({"test.py": "backup.py"}, mock_backup_manager)

        # Run version bump
        runner = CliRunner()
        result = runner.invoke(main, [])

        # Verify backup and history operations were called
        assert result.exit_code == 0
        mock_backup_files.assert_called_once()
        mock_backup_manager.store_operation_history.assert_called_once()

        # Verify the history call contains expected data
        call_args = mock_backup_manager.store_operation_history.call_args
        assert call_args[1]["version"] == "2025.10.12"
        assert call_args[1]["files_updated"] == ["test.py"]
        assert call_args[1]["backups"] == {"test.py": "backup.py"}

    @mock.patch('subprocess.run')
    @mock.patch('src.bumpcalver.cli.BackupManager')
    @mock.patch('src.bumpcalver.cli.backup_files_before_update')
    @mock.patch('src.bumpcalver.cli.load_config')
    @mock.patch('src.bumpcalver.cli.update_version_in_files')
    @mock.patch('src.bumpcalver.cli.get_current_datetime_version')
    def test_version_bump_with_git_creates_complete_history(
        self,
        mock_get_version,
        mock_update_files,
        mock_load_config,
        mock_backup_files,
        mock_backup_manager_class,
        mock_subprocess_run
    ):
        """Test that version bump with git operations creates complete history."""
        # Setup mocks
        mock_backup_manager = mock.Mock()
        mock_backup_manager_class.return_value = mock_backup_manager

        mock_load_config.return_value = {
            "version_format": "{current_date}",
            "date_format": "%Y.%m.%d",
            "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
            "timezone": "UTC",
            "git_tag": True,
            "auto_commit": True,
        }

        mock_get_version.return_value = "2025.10.12"
        mock_update_files.return_value = ["test.py"]
        mock_backup_files.return_value = ({"test.py": "backup.py"}, mock_backup_manager)

        # Mock git commands
        mock_subprocess_run.return_value = mock.Mock(stdout="abc123def\n", returncode=0)

        # Run version bump with git
        runner = CliRunner()
        result = runner.invoke(main, [])

        # Verify backup and history operations were called
        assert result.exit_code == 0
        mock_backup_manager.store_operation_history.assert_called_once()

        # Verify the history call contains git information
        call_args = mock_backup_manager.store_operation_history.call_args
        assert call_args[1]["git_tag"] is True
        assert call_args[1]["git_commit"] is True
        assert call_args[1]["git_tag_name"] == "2025.10.12"
