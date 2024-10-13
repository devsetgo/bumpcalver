# tests/test_config.py
import os
import sys
from unittest import mock

import toml
from src.bumpcalver.config import load_config


def test_load_config_with_valid_pyproject(monkeypatch):
    # Mock os.path.exists to return True
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    # Mock the content of pyproject.toml
    pyproject_content = {
        "tool": {
            "bumpcalver": {
                "version_format": "{current_date}-{build_count:03}",
                "timezone": "UTC",
                "file": [
                    {
                        "path": "src/__init__.py",
                        "file_type": "python",
                        "variable": "__version__",
                    }
                ],
                "git_tag": True,
                "auto_commit": True,
            }
        }
    }

    # Mock toml.load
    def mock_toml_load(f):
        return pyproject_content

    monkeypatch.setattr(toml, "load", mock_toml_load)

    # Mock parse_dot_path
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Capture the print output
    with mock.patch("builtins.print"):
        config = load_config()

    # Assertions (same as before)
    assert config["version_format"] == "{current_date}-{build_count:03}"
    # ... rest of the assertions ...


def test_load_config_with_malformed_pyproject(monkeypatch):
    # Mock os.path.exists to return True
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    # Mock toml.load to raise TomlDecodeError
    def mock_toml_load(f):
        raise toml.TomlDecodeError("Error", "abc", 0)

    monkeypatch.setattr(toml, "load", mock_toml_load)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Mock sys.exit to prevent exiting the test runner
    exit_mock = mock.Mock()
    monkeypatch.setattr(sys, "exit", exit_mock)

    # Capture the print output
    with mock.patch("builtins.print") as mock_print:
        load_config()

    # Extract printed messages
    printed_messages = [args[0] for args, kwargs in mock_print.call_args_list]

    # Assertions
    assert any(
        msg.startswith("Error parsing pyproject.toml: Error")
        for msg in printed_messages
    )
    exit_mock.assert_called_once_with(1)


def test_load_config_pyproject_not_found(monkeypatch):
    # Mock os.path.exists to return False
    monkeypatch.setattr(os.path, "exists", lambda x: False)

    # Capture the print output
    with mock.patch("builtins.print") as mock_print:
        config = load_config()

    # Assertions
    mock_print.assert_any_call("pyproject.toml not found. Using default configuration.")
    assert config == {}


def test_load_config_with_missing_values(monkeypatch):
    # Mock os.path.exists to return True
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    # Mock the content of pyproject.toml with missing configurations
    pyproject_content = {
        "tool": {
            "bumpcalver": {
                # Missing configurations
            }
        }
    }

    # Mock toml.load
    def mock_toml_load(f):
        return pyproject_content

    monkeypatch.setattr(toml, "load", mock_toml_load)

    # Mock parse_dot_path (should not be called)
    parse_dot_path_mock = mock.Mock()
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", parse_dot_path_mock)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Capture the print output
    with mock.patch("builtins.print"):
        config = load_config()

    # Assertions (same as before)
    assert config["version_format"] == "{current_date}-{build_count:03}"
    # ... rest of the assertions ...

    # Ensure parse_dot_path was not called
    parse_dot_path_mock.assert_not_called()
