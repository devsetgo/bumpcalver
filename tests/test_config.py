import os
import sys
from unittest import mock

import toml
from src.bumpcalver.config import load_config


def test_load_config_with_valid_pyproject(monkeypatch):
    # Mock os.path.exists to return True for pyproject.toml
    monkeypatch.setattr(os.path, "exists", lambda x: x == "pyproject.toml")

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

    assert config["version_format"] == "{current_date}-{build_count:03}"
    assert config["timezone"] == "UTC"
    assert config["file_configs"] == [
        {
            "path": "src/__init__.py",
            "file_type": "python",
            "variable": "__version__",
        }
    ]
    assert config["git_tag"] is True
    assert config["auto_commit"] is True


def test_load_config_with_valid_bumpcalver(monkeypatch):
    # Mock os.path.exists to return True for bumpcalver.toml
    monkeypatch.setattr(os.path, "exists", lambda x: x == "bumpcalver.toml")

    # Mock the content of bumpcalver.toml
    bumpcalver_content = {
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

    # Mock toml.load
    def mock_toml_load(f):
        return bumpcalver_content

    monkeypatch.setattr(toml, "load", mock_toml_load)

    # Mock parse_dot_path
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Capture the print output
    with mock.patch("builtins.print"):
        config = load_config()

    assert config["version_format"] == "{current_date}-{build_count:03}"
    assert config["timezone"] == "UTC"
    assert config["file_configs"] == [
        {
            "path": "src/__init__.py",
            "file_type": "python",
            "variable": "__version__",
        }
    ]
    assert config["git_tag"] is True
    assert config["auto_commit"] is True


def test_load_config_with_malformed_pyproject(monkeypatch):
    # Mock os.path.exists to return True for pyproject.toml
    monkeypatch.setattr(os.path, "exists", lambda x: x == "pyproject.toml")

    # Mock toml.load to raise a TomlDecodeError
    def mock_toml_load(f):
        raise toml.TomlDecodeError("Error", "pyproject.toml", 0)

    monkeypatch.setattr(toml, "load", mock_toml_load)

    # Mock parse_dot_path
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Capture the print output
    with mock.patch("builtins.print") as mock_print:
        config = load_config()

    mock_print.assert_any_call(
        "Error decoding pyproject.toml: Error (line 1 column 1 char 0)", file=sys.stderr
    )
    assert config == {}


def test_load_config_pyproject_not_found(monkeypatch):
    # Mock os.path.exists to return False for pyproject.toml and True for bumpcalver.toml
    monkeypatch.setattr(os.path, "exists", lambda x: x == "bumpcalver.toml")

    # Mock the content of bumpcalver.toml
    bumpcalver_content = {
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

    # Mock toml.load
    def mock_toml_load(f):
        return bumpcalver_content

    monkeypatch.setattr(toml, "load", mock_toml_load)

    # Mock parse_dot_path
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Capture the print output
    with mock.patch("builtins.print"):
        config = load_config()

    assert config["version_format"] == "{current_date}-{build_count:03}"
    assert config["timezone"] == "UTC"
    assert config["file_configs"] == [
        {
            "path": "src/__init__.py",
            "file_type": "python",
            "variable": "__version__",
        }
    ]
    assert config["git_tag"] is True
    assert config["auto_commit"] is True


def test_load_config_with_generic_exception(monkeypatch):
    # Mock os.path.exists to return True for pyproject.toml
    monkeypatch.setattr(os.path, "exists", lambda x: x == "pyproject.toml")

    # Mock toml.load to raise a generic exception
    def mock_toml_load(f):
        raise Exception("Generic error")

    monkeypatch.setattr(toml, "load", mock_toml_load)

    # Mock parse_dot_path
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Capture the print output
    with mock.patch("builtins.print") as mock_print:
        config = load_config()

    mock_print.assert_any_call(
        "Error loading configuration from pyproject.toml: Generic error",
        file=sys.stderr,
    )
    assert config == {}


def test_load_config_no_config_file_found(monkeypatch):
    # Mock os.path.exists to return False for both pyproject.toml and bumpcalver.toml
    monkeypatch.setattr(os.path, "exists", lambda x: False)

    # Mock parse_dot_path
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    # Mock open
    monkeypatch.setattr("builtins.open", mock.mock_open())

    # Capture the print output
    with mock.patch("builtins.print") as mock_print:
        config = load_config()

    mock_print.assert_any_call(
        "No configuration file found. Please create either pyproject.toml or bumpcalver.toml.",
        file=sys.stderr,
    )
    assert config == {}


def test_load_config_reads_suffix_formats(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: x == "pyproject.toml")
    content = {
        "tool": {
            "bumpcalver": {
                "version_format": "{current_date}.{build_count}",
                "file": [],
                "beta_format": "b{beta_count}",
                "rc_format": "rc{rc_count}",
                "release_format": ".final",
            }
        }
    }
    monkeypatch.setattr(toml, "load", lambda f: content)
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    config = load_config()

    assert config["beta_format"] == "b{beta_count}"
    assert config["rc_format"] == "rc{rc_count}"
    assert config["release_format"] == ".final"


def test_load_config_suffix_format_defaults(monkeypatch):
    monkeypatch.setattr(os.path, "exists", lambda x: x == "pyproject.toml")
    content = {"tool": {"bumpcalver": {"version_format": "{current_date}.{build_count}", "file": []}}}
    monkeypatch.setattr(toml, "load", lambda f: content)
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    config = load_config()

    assert config["beta_format"] == ".beta"
    assert config["rc_format"] == ".rc"
    assert config["release_format"] == ".release"
