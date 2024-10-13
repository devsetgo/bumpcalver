# tests/test_cli.py

from unittest import mock

from click.testing import CliRunner
from src.bumpcalver.cli import main


def test_beta_option():
    runner = CliRunner()
    result = runner.invoke(main, ["--beta"])
    assert result.exit_code == 0
    # Add assertions to check the expected behavior when --beta is used


def test_rc_option():
    runner = CliRunner()
    result = runner.invoke(main, ["--rc"])
    assert result.exit_code == 0
    # Add assertions to check the expected behavior when --rc is used


def test_release_option():
    runner = CliRunner()
    result = runner.invoke(main, ["--release"])
    assert result.exit_code == 0
    # Add assertions to check the expected behavior when --release is used


def test_custom_option():
    runner = CliRunner()
    result = runner.invoke(main, ["--custom", "1.2.3"])
    assert result.exit_code == 0
    # Add assertions to check the expected behavior when --custom is used


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


def test_no_options():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_build_option(monkeypatch):
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
