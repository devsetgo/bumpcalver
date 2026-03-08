# tests/test_cli.py

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
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda: mock_config)

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
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda: mock_config)

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
    monkeypatch.setattr("src.bumpcalver.cli.BackupManager", lambda: mock_backup_manager_instance)

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
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda: mock_config)

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
    monkeypatch.setattr("src.bumpcalver.cli.load_config", lambda: mock_config)

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
