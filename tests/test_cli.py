# tests/test_cli.py

from unittest import mock
from click.testing import CliRunner
from src.bumpcalver.cli import main


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
