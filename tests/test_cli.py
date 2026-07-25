# tests/test_cli.py

import os
import tempfile
import subprocess
from unittest import mock
from click.testing import CliRunner
from src.bumpcalver.cli import main
from src.bumpcalver import __version__


def test_version_option():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_beta_option(mock_load_config, mock_get_current_datetime_version, mock_update_version_in_files):
    # Mock configuration
    mock_load_config.return_value = {
        "version_format": "{current_date}-{build_count:03}",
        "date_format": "%Y-%m-%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }
    mock_get_current_datetime_version.return_value = "2025-08-03"
    mock_update_version_in_files.return_value = ["test.py"]

    runner = CliRunner()
    result = runner.invoke(main, ["--beta"])
    assert result.exit_code == 0
    # Verify that the version includes beta suffix
    mock_update_version_in_files.assert_called_once_with("2025-08-03.beta", mock.ANY)


@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_rc_option(mock_load_config, mock_get_current_datetime_version, mock_update_version_in_files):
    # Mock configuration
    mock_load_config.return_value = {
        "version_format": "{current_date}-{build_count:03}",
        "date_format": "%Y-%m-%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }
    mock_get_current_datetime_version.return_value = "2025-08-03"
    mock_update_version_in_files.return_value = ["test.py"]

    runner = CliRunner()
    result = runner.invoke(main, ["--rc"])
    assert result.exit_code == 0
    # Verify that the version includes rc suffix
    mock_update_version_in_files.assert_called_once_with("2025-08-03.rc", mock.ANY)


@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_release_option(mock_load_config, mock_get_current_datetime_version, mock_update_version_in_files):
    # Mock configuration
    mock_load_config.return_value = {
        "version_format": "{current_date}-{build_count:03}",
        "date_format": "%Y-%m-%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }
    mock_get_current_datetime_version.return_value = "2025-08-03"
    mock_update_version_in_files.return_value = ["test.py"]

    runner = CliRunner()
    result = runner.invoke(main, ["--release"])
    assert result.exit_code == 0
    # Verify that the version includes release suffix
    mock_update_version_in_files.assert_called_once_with("2025-08-03.release", mock.ANY)


@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_custom_option(mock_load_config, mock_get_current_datetime_version, mock_update_version_in_files):
    # Mock configuration
    mock_load_config.return_value = {
        "version_format": "{current_date}-{build_count:03}",
        "date_format": "%Y-%m-%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }
    mock_get_current_datetime_version.return_value = "2025-08-03"
    mock_update_version_in_files.return_value = ["test.py"]

    runner = CliRunner()
    result = runner.invoke(main, ["--custom", "1.2.3"])
    assert result.exit_code == 0
    # Verify that the version includes custom suffix
    mock_update_version_in_files.assert_called_once_with("2025-08-03.1.2.3", mock.ANY)


def test_beta_and_rc_options():
    runner = CliRunner()
    result = runner.invoke(main, ["--beta", "--rc"])
    assert result.exit_code != 0
    assert (
        "Error: Only one of --beta, --rc, --release, or --custom can be set at a time."
        in result.output
    )


def test_beta_and_release_options():
    runner = CliRunner()
    result = runner.invoke(main, ["--beta", "--release"])
    assert result.exit_code != 0
    assert (
        "Error: Only one of --beta, --rc, --release, or --custom can be set at a time."
        in result.output
    )


def test_rc_and_custom_options():
    runner = CliRunner()
    result = runner.invoke(main, ["--rc", "--custom", "1.2.3"])
    assert result.exit_code != 0
    assert (
        "Error: Only one of --beta, --rc, --release, or --custom can be set at a time."
        in result.output
    )


def test_all_options():
    runner = CliRunner()
    result = runner.invoke(main, ["--beta", "--rc", "--release", "--custom", "1.2.3"])
    assert result.exit_code != 0
    assert (
        "Error: Only one of --beta, --rc, --release, or --custom can be set at a time."
        in result.output
    )


@mock.patch('src.bumpcalver.cli.load_config')
def test_no_options(mock_load_config):
    # Mock configuration with empty file_configs to avoid file operations
    mock_load_config.return_value = {
        "version_format": "{current_date}-{build_count:03}",
        "date_format": "%Y-%m-%d",
        "file_configs": [],  # Empty to trigger the "No files specified" message
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_build_option(monkeypatch):
    # Mock configuration
    mock_config = {
        "version_format": "{current_date}-{build_count:03}",
        "date_format": "%Y.%m.%d",
        "file_configs": [
            {
                "path": "dummy/path/to/file",
                "file_type": "python",
                "variable": "__version__",
            }
        ],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)

    # Mock get_build_version
    mock_get_build_version = mock.Mock(return_value="2023-10-10-001")
    monkeypatch.setattr("src.bumpcalver.cli.get_build_version", mock_get_build_version)

    # Avoid touching the filesystem in this unit test
    monkeypatch.setattr(
        "src.bumpcalver.cli.update_version_in_files",
        lambda new_version, file_configs: [file_configs[0]["path"]],
    )

    mock_backup_files_before_update = mock.Mock(return_value=({}, mock.Mock()))
    monkeypatch.setattr(
        "src.bumpcalver.cli.backup_files_before_update", mock_backup_files_before_update
    )

    mock_backup_manager_cls = mock.Mock()
    mock_backup_manager_instance = mock.Mock()
    mock_backup_manager_cls.return_value = mock_backup_manager_instance
    monkeypatch.setattr("src.bumpcalver.cli.BackupManager", mock_backup_manager_cls)

    # Run the CLI command with the --build option
    runner = CliRunner()
    result = runner.invoke(main, ["--build"])

    # Verify that get_build_version was called with the correct parameters
    mock_get_build_version.assert_called_once_with(
        mock_config["file_configs"][0],
        mock_config["version_format"],
        mock_config["timezone"],
        mock_config["date_format"],
        major=0,
        minor=0,
        patch=0,
    )

    # Verify the output
    assert result.exit_code == 0
    assert "Updated version to 2023-10-10-001 in specified files." in result.output


def test_build_option_noop_does_not_create_history(monkeypatch):
    mock_config = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%-m.%-d",
        "file_configs": [
            {"path": "test.py", "file_type": "python", "variable": "__version__"}
        ],
        "timezone": "UTC",
        "git_tag": True,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)

    # Computed new version equals current version
    monkeypatch.setattr("src.bumpcalver.cli.get_build_version", lambda *a, **k: "26.3.7.1")

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "26.3.7.1"
    monkeypatch.setattr("src.bumpcalver.cli.get_version_handler", lambda ft: mock_handler)

    mock_update = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.update_version_in_files", mock_update)

    mock_backup = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.backup_files_before_update", mock_backup)

    mock_store_history = mock.Mock()
    mock_backup_manager_instance = mock.Mock()
    mock_backup_manager_instance.store_operation_history = mock_store_history
    monkeypatch.setattr("src.bumpcalver.cli.BackupManager", lambda *args, **kwargs: mock_backup_manager_instance)

    mock_git_tag = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.create_git_tag", mock_git_tag)

    runner = CliRunner()
    result = runner.invoke(main, ["--build", "--git-tag"])

    assert result.exit_code == 0
    assert "Version already set to 26.3.7.1" in result.output
    mock_update.assert_not_called()
    mock_backup.assert_not_called()
    mock_store_history.assert_not_called()
    mock_git_tag.assert_not_called()


def test_build_option_noop_with_directive_does_not_create_history(monkeypatch):
    """Cover directive-based read_version path in the no-op guard."""
    mock_config = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%-m.%-d",
        "file_configs": [
            {
                "path": "Dockerfile",
                "file_type": "dockerfile",
                "variable": "APP_VERSION",
                "directive": "ARG",
            }
        ],
        "timezone": "UTC",
        "git_tag": True,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)

    monkeypatch.setattr(
        "src.bumpcalver.cli.get_build_version", lambda *a, **k: "26.3.7.1"
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "26.3.7.1"
    monkeypatch.setattr("src.bumpcalver.cli.get_version_handler", lambda ft: mock_handler)

    mock_update = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.update_version_in_files", mock_update)
    mock_backup = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.backup_files_before_update", mock_backup)

    mock_backup_manager_instance = mock.Mock()
    mock_backup_manager_instance.store_operation_history = mock.Mock()
    monkeypatch.setattr(
        "src.bumpcalver.cli.BackupManager", lambda *args, **kwargs: mock_backup_manager_instance
    )
    mock_git_tag = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.create_git_tag", mock_git_tag)

    runner = CliRunner()
    result = runner.invoke(main, ["--build", "--git-tag"])

    assert result.exit_code == 0
    assert "Version already set to 26.3.7.1" in result.output
    mock_handler.read_version.assert_called_once()
    # Ensure the directive path was used
    assert mock_handler.read_version.call_args.kwargs.get("directive") == "ARG"
    mock_update.assert_not_called()
    mock_backup.assert_not_called()
    mock_backup_manager_instance.store_operation_history.assert_not_called()
    mock_git_tag.assert_not_called()


def test_noop_guard_read_exception_falls_through_to_update(monkeypatch):
    """If the no-op guard can't read a file version, it should proceed to update."""
    mock_config = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%-m.%-d",
        "file_configs": [
            {"path": "test.py", "file_type": "python", "variable": "__version__"}
        ],
        "timezone": "UTC",
        "git_tag": False,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)
    monkeypatch.setattr(
        "src.bumpcalver.cli.get_build_version", lambda *a, **k: "26.3.7.1"
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.side_effect = RuntimeError("boom")
    monkeypatch.setattr("src.bumpcalver.cli.get_version_handler", lambda ft: mock_handler)

    mock_backup_manager_instance = mock.Mock()
    mock_backup_manager_instance.store_operation_history = mock.Mock()
    monkeypatch.setattr(
        "src.bumpcalver.cli.BackupManager", lambda *args, **kwargs: mock_backup_manager_instance
    )

    mock_backup = mock.Mock(return_value=({}, mock_backup_manager_instance))
    monkeypatch.setattr("src.bumpcalver.cli.backup_files_before_update", mock_backup)

    mock_update = mock.Mock(return_value=[os.path.join(os.getcwd(), "test.py")])
    monkeypatch.setattr("src.bumpcalver.cli.update_version_in_files", mock_update)

    runner = CliRunner()
    result = runner.invoke(main, ["--build"])

    assert result.exit_code == 0
    mock_backup.assert_called_once()
    mock_update.assert_called_once()
    mock_backup_manager_instance.store_operation_history.assert_called_once()


def test_no_files_updated_removes_backups_and_skips_history(monkeypatch):
    """Cover the no-op-after-update branch that cleans up created backups."""
    mock_config = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%-m.%-d",
        "file_configs": [
            {"path": "test.py", "file_type": "python", "variable": "__version__"}
        ],
        "timezone": "UTC",
        "git_tag": True,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)
    monkeypatch.setattr(
        "src.bumpcalver.cli.get_build_version", lambda *a, **k: "26.3.7.1"
    )

    # Ensure we don't trip the early no-op guard
    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "0.0.0"
    monkeypatch.setattr("src.bumpcalver.cli.get_version_handler", lambda ft: mock_handler)

    backup_fd, backup_path = tempfile.mkstemp(prefix="bumpcalver_backup_")
    os.close(backup_fd)
    assert os.path.exists(backup_path)

    mock_backup_manager_instance = mock.Mock()
    mock_backup_manager_instance.store_operation_history = mock.Mock()
    monkeypatch.setattr(
        "src.bumpcalver.cli.BackupManager", lambda *args, **kwargs: mock_backup_manager_instance
    )

    backups = {os.path.join(os.getcwd(), "test.py"): backup_path}
    monkeypatch.setattr(
        "src.bumpcalver.cli.backup_files_before_update",
        lambda file_configs, backup_manager: (backups, backup_manager),
    )

    monkeypatch.setattr(
        "src.bumpcalver.cli.update_version_in_files", lambda *a, **k: []
    )
    mock_git_tag = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.create_git_tag", mock_git_tag)

    runner = CliRunner()
    result = runner.invoke(main, ["--build", "--git-tag"])

    assert result.exit_code == 0
    assert "No files were updated" in result.output
    assert not os.path.exists(backup_path)
    mock_backup_manager_instance.store_operation_history.assert_not_called()
    mock_git_tag.assert_not_called()


def test_no_files_updated_backup_cleanup_exception_is_swallowed(monkeypatch):
    """Cover the cleanup exception branch inside the no-files-updated path."""
    mock_config = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%-m.%-d",
        "file_configs": [
            {"path": "test.py", "file_type": "python", "variable": "__version__"}
        ],
        "timezone": "UTC",
        "git_tag": False,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)
    monkeypatch.setattr(
        "src.bumpcalver.cli.get_build_version", lambda *a, **k: "26.3.7.1"
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "0.0.0"
    monkeypatch.setattr("src.bumpcalver.cli.get_version_handler", lambda ft: mock_handler)

    mock_backup_manager_instance = mock.Mock()
    mock_backup_manager_instance.store_operation_history = mock.Mock()
    monkeypatch.setattr(
        "src.bumpcalver.cli.BackupManager", lambda *args, **kwargs: mock_backup_manager_instance
    )

    backups = {os.path.join(os.getcwd(), "test.py"): "/tmp/backup_should_fail_remove"}
    monkeypatch.setattr(
        "src.bumpcalver.cli.backup_files_before_update",
        lambda file_configs, backup_manager: (backups, backup_manager),
    )
    monkeypatch.setattr(
        "src.bumpcalver.cli.update_version_in_files", lambda *a, **k: []
    )

    monkeypatch.setattr("src.bumpcalver.cli.os.path.exists", lambda p: True)

    def _raise_remove(_p: str) -> None:
        raise OSError("cannot remove")

    monkeypatch.setattr("src.bumpcalver.cli.os.remove", _raise_remove)

    runner = CliRunner()
    result = runner.invoke(main, ["--build"])
    assert result.exit_code == 0
    assert "No files were updated" in result.output
    mock_backup_manager_instance.store_operation_history.assert_not_called()


def test_list_history_option(monkeypatch):
    mock_list = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.cli.list_undo_history", mock_list)
    runner = CliRunner()
    result = runner.invoke(main, ["--list-history"])
    assert result.exit_code == 0
    mock_list.assert_called_once()


def test_undo_option_exit_codes(monkeypatch):
    monkeypatch.setattr("src.bumpcalver.cli.undo_last_operation", lambda: True)
    runner = CliRunner()
    result = runner.invoke(main, ["--undo"])
    assert result.exit_code == 0


def test_undo_id_option_exit_codes(monkeypatch):
    monkeypatch.setattr("src.bumpcalver.cli.undo_operation_by_id", lambda _id: False)
    runner = CliRunner()
    result = runner.invoke(main, ["--undo-id", "abc"])
    assert result.exit_code == 1


def test_undo_options_conflict_with_bump_options():
    runner = CliRunner()
    result = runner.invoke(main, ["--build", "--undo"])
    assert result.exit_code != 0
    assert "Undo options" in result.output


def test_value_error(monkeypatch):
    # Mock configuration
    mock_config = {
        "version_format": "{current_date}-{build_count:03}",
        "file_configs": [
            {
                "path": "dummy/path/to/file",
                "file_type": "python",
                "variable": "__version__",
            }
        ],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)

    # Mock get_build_version to raise ValueError
    mock_get_build_version = mock.Mock(side_effect=ValueError("Invalid value"))
    monkeypatch.setattr("src.bumpcalver.cli.get_build_version", mock_get_build_version)

    # Run the CLI command with the --build option
    runner = CliRunner()
    result = runner.invoke(main, ["--build"])

    # Verify the output
    assert result.exit_code == 1
    assert "Error generating version: Invalid value" in result.output


def test_key_error(monkeypatch):
    # Mock configuration
    mock_config = {
        "version_format": "{current_date}-{build_count:03}",
        "file_configs": [
            {
                "path": "dummy/path/to/file",
                "file_type": "python",
                "variable": "__version__",
            }
        ],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
    }
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda *args, **kwargs: mock_config)

    # Mock get_build_version to raise KeyError
    mock_get_build_version = mock.Mock(side_effect=KeyError("Missing key"))
    monkeypatch.setattr("src.bumpcalver.cli.get_build_version", mock_get_build_version)

    # Run the CLI command with the --build option
    runner = CliRunner()
    result = runner.invoke(main, ["--build"])

    # Verify the output
    assert result.exit_code == 1
    assert "Error generating version: 'Missing key'" in result.output


@mock.patch('src.bumpcalver.cli.subprocess')
@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_git_operations_exception_handling(mock_load_config, mock_get_current_datetime_version,
                                           mock_update_version_in_files, mock_subprocess):
    """Test CLI handling of git operation exceptions."""
    # Mock configuration with git operations enabled
    mock_load_config.return_value = {
        "version_format": "{current_date}",
        "date_format": "%Y.%m.%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "UTC",
        "git_tag": True,
        "auto_commit": True,
    }
    mock_get_current_datetime_version.return_value = "2025.01.01"
    mock_update_version_in_files.return_value = ["test.py"]

    # Mock subprocess to raise CalledProcessError for git operations
    mock_subprocess.CalledProcessError = subprocess.CalledProcessError
    mock_subprocess.run.side_effect = subprocess.CalledProcessError(1, "git")

    runner = CliRunner()
    result = runner.invoke(main, [])

    # Should complete successfully despite git operation failure
    assert result.exit_code == 0


@mock.patch('src.bumpcalver.cli.BackupManager')
@mock.patch('src.bumpcalver.cli.subprocess.run')
@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_git_tag_subprocess_exception(mock_load_config, mock_get_current_datetime_version,
                                     mock_update_version_in_files, mock_subprocess_run, mock_backup_manager):
    """Test CLI handling of subprocess CalledProcessError during git tag operations."""
    # Mock configuration with git tag enabled
    mock_load_config.return_value = {
        "version_format": "{current_date}",
        "date_format": "%Y.%m.%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "UTC",
        "git_tag": True,
        "auto_commit": False,
    }
    mock_get_current_datetime_version.return_value = "2025.01.01"
    mock_update_version_in_files.return_value = ["test.py"]

    # Mock BackupManager
    mock_backup_instance = mock_backup_manager.return_value
    mock_backup_instance.create_backups.return_value = {"test.py": "backup.py"}

    # Mock subprocess.run to raise CalledProcessError for git rev-parse
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "git rev-parse HEAD")

    runner = CliRunner()
    result = runner.invoke(main, [])

    # Should complete successfully despite git operation failure (line 186)
    assert result.exit_code == 0
    # Verify store_operation_history was called (lines 190-192)
    mock_backup_instance.store_operation_history.assert_called_once()


@mock.patch('src.bumpcalver.cli.get_version_handler')
@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_beta_custom_format_no_existing(
    mock_load_config, mock_get_dt, mock_update, mock_get_handler
):
    """beta_format = 'b{beta_count}' with no existing version produces 'b1'."""
    mock_load_config.return_value = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%m.%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
        "beta_format": "b{beta_count}",
    }
    mock_get_dt.return_value = "26.05.24"
    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = None
    mock_get_handler.return_value = mock_handler
    mock_update.return_value = ["test.py"]

    runner = CliRunner()
    result = runner.invoke(main, ["--beta"])
    assert result.exit_code == 0
    mock_update.assert_called_once_with("26.05.24b1", mock.ANY)


@mock.patch('src.bumpcalver.cli.get_version_handler')
@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_beta_custom_format_increments_count(
    mock_load_config, mock_get_dt, mock_update, mock_get_handler
):
    """beta_format = 'b{beta_count}' increments when current version matches base."""
    mock_load_config.return_value = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%m.%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
        "beta_format": "b{beta_count}",
    }
    mock_get_dt.return_value = "26.05.24"
    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "26.05.24b1"
    mock_get_handler.return_value = mock_handler
    mock_update.return_value = ["test.py"]

    runner = CliRunner()
    result = runner.invoke(main, ["--beta"])
    assert result.exit_code == 0
    mock_update.assert_called_once_with("26.05.24b2", mock.ANY)


@mock.patch('src.bumpcalver.cli.get_version_handler')
@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_rc_custom_format(mock_load_config, mock_get_dt, mock_update, mock_get_handler):
    """rc_format is read from config and honoured."""
    mock_load_config.return_value = {
        "version_format": "{current_date}.{build_count}",
        "date_format": "%y.%m.%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": False,
        "auto_commit": False,
        "rc_format": "rc{rc_count}",
    }
    mock_get_dt.return_value = "26.05.24"
    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = None
    mock_get_handler.return_value = mock_handler
    mock_update.return_value = ["test.py"]

    runner = CliRunner()
    result = runner.invoke(main, ["--rc"])
    assert result.exit_code == 0
    mock_update.assert_called_once_with("26.05.24rc1", mock.ANY)


# ---------------------------------------------------------------------------
# --dry-run (Capability Expansion §5.3)
# ---------------------------------------------------------------------------

@mock.patch('src.bumpcalver.cli.update_version_in_files')
@mock.patch('src.bumpcalver.cli.create_git_tag')
@mock.patch('src.bumpcalver.cli.get_current_datetime_version')
@mock.patch('src.bumpcalver.cli.load_config')
def test_dry_run_does_not_write_files_or_create_git_tag(
    mock_load_config, mock_get_current_datetime_version, mock_create_git_tag, mock_update_version_in_files
):
    mock_load_config.return_value = {
        "version_format": "{current_date}-{build_count:03}",
        "date_format": "%Y-%m-%d",
        "file_configs": [{"path": "test.py", "file_type": "python", "variable": "__version__"}],
        "timezone": "America/New_York",
        "git_tag": True,
        "auto_commit": False,
    }
    mock_get_current_datetime_version.return_value = "2025-08-03"

    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run"])

    assert result.exit_code == 0
    mock_update_version_in_files.assert_not_called()
    mock_create_git_tag.assert_not_called()
    assert "[dry-run] Would bump version to 2025-08-03 in:" in result.output
    assert "test.py" in result.output
    assert "Would create git tag '2025-08-03'" in result.output


def test_dry_run_leaves_real_files_and_repo_state_untouched():
    # End-to-end, real filesystem (no mocking of update_version_in_files):
    # the strongest proof --dry-run doesn't write anything is to actually
    # run it against a real file and check nothing on disk changed.
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("version.py", "w") as f:
            f.write('__version__ = "2020.01.01.001"\n')
        with open("bumpcalver.toml", "w") as f:
            f.write(
                'version_format = "{current_date}.{build_count:03}"\n'
                'date_format = "%Y.%m.%d"\n\n'
                '[[file]]\n'
                'path = "version.py"\n'
                'file_type = "python"\n'
                'variable = "__version__"\n'
            )
        original_content = open("version.py").read()

        result = runner.invoke(main, ["--build", "--dry-run"])

        assert result.exit_code == 0
        assert "[dry-run] Would bump version to" in result.output
        assert "version.py" in result.output
        assert open("version.py").read() == original_content
        assert not os.path.exists(".bumpcalver")
        assert not os.path.exists("bumpcalver-history.json")


def test_dry_run_reports_no_op_without_writing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("version.py", "w") as f:
            f.write('__version__ = "2026.01.01.001"\n')
        with open("bumpcalver.toml", "w") as f:
            f.write(
                'version_format = "{current_date}.{build_count:03}"\n'
                'date_format = "%Y.%m.%d"\n\n'
                '[[file]]\n'
                'path = "version.py"\n'
                'file_type = "python"\n'
                'variable = "__version__"\n'
            )

        with mock.patch(
            "src.bumpcalver.cli.get_current_datetime_version", return_value="2026.01.01"
        ), mock.patch(
            "src.bumpcalver.cli.get_build_version", return_value="2026.01.01.001"
        ):
            result = runner.invoke(main, ["--build", "--dry-run"])

        assert result.exit_code == 0
        assert "[dry-run] Version already set to 2026.01.01.001; no files would be updated." in result.output
        assert not os.path.exists(".bumpcalver")


def test_dry_run_conflicts_with_undo():
    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run", "--undo"])
    assert result.exit_code != 0
    assert "--dry-run cannot be used with --undo" in result.output


# ---------------------------------------------------------------------------
# --config-file / BUMPCALVER_CONFIG (Capability Expansion §5.4)
# ---------------------------------------------------------------------------

def test_config_file_option_resolves_paths_relative_to_config_location(tmp_path):
    # The whole point: invoke from an unrelated cwd, point --config-file at a
    # project living elsewhere, and confirm the *target project's* file gets
    # updated — not something (nonexistent) relative to the invoking cwd.
    project_dir = tmp_path / "actual_project"
    project_dir.mkdir()
    (project_dir / "version.py").write_text('__version__ = "2020.01.01.001"\n', encoding="utf-8")
    (project_dir / "bumpcalver.toml").write_text(
        'version_format = "{current_date}.{build_count:03}"\n'
        'date_format = "%Y.%m.%d"\n\n'
        '[[file]]\n'
        'path = "version.py"\n'
        'file_type = "python"\n'
        'variable = "__version__"\n',
        encoding="utf-8",
    )
    config_path = str(project_dir / "bumpcalver.toml")

    runner = CliRunner()
    with runner.isolated_filesystem():
        # cwd here is a brand-new, empty temp dir with no version.py at all.
        result = runner.invoke(main, ["--build", "--config-file", config_path])
        cwd_has_no_version_py = not os.path.exists("version.py")

    assert result.exit_code == 0, result.output
    assert cwd_has_no_version_py
    updated_content = (project_dir / "version.py").read_text(encoding="utf-8")
    assert "2020.01.01.001" not in updated_content
    assert "__version__" in updated_content
    # Backups/undo history are colocated with the actual project, not the cwd.
    assert (project_dir / "bumpcalver-history.json").exists()
    assert (project_dir / ".bumpcalver" / "backups").is_dir()


def test_config_file_env_var(tmp_path, monkeypatch):
    project_dir = tmp_path / "actual_project"
    project_dir.mkdir()
    (project_dir / "version.py").write_text('__version__ = "2020.01.01.001"\n', encoding="utf-8")
    (project_dir / "bumpcalver.toml").write_text(
        'version_format = "{current_date}.{build_count:03}"\n'
        'date_format = "%Y.%m.%d"\n\n'
        '[[file]]\n'
        'path = "version.py"\n'
        'file_type = "python"\n'
        'variable = "__version__"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("BUMPCALVER_CONFIG", str(project_dir / "bumpcalver.toml"))

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["--build"])

    assert result.exit_code == 0, result.output
    updated_content = (project_dir / "version.py").read_text(encoding="utf-8")
    assert "2020.01.01.001" not in updated_content


def test_config_file_nonexistent_path_rejected_by_click():
    runner = CliRunner()
    result = runner.invoke(main, ["--build", "--config-file", "/no/such/file.toml"])
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "Error" in result.output


def test_config_file_conflicts_with_undo(tmp_path):
    config_file = tmp_path / "bumpcalver.toml"
    config_file.write_text('version_format = "x"\nfile = []\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["--config-file", str(config_file), "--undo"])
    assert result.exit_code != 0
    assert "--config-file cannot be used with --undo" in result.output
