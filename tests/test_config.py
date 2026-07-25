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
    content = {
        "tool": {"bumpcalver": {"version_format": "{current_date}.{build_count}", "file": []}}
    }
    monkeypatch.setattr(toml, "load", lambda f: content)
    monkeypatch.setattr("src.bumpcalver.config.parse_dot_path", lambda x, y: x)

    config = load_config()

    assert config["beta_format"] == ".beta"
    assert config["rc_format"] == ".rc"
    assert config["release_format"] == ".release"


# ---------------------------------------------------------------------------
# load_config(config_path=...) — explicit config file (Capability Expansion
# §5.4: --config-file / BUMPCALVER_CONFIG). Real temp files rather than
# mocking os.path.exists/toml.load, since the whole point of this parameter
# is bypassing auto-discovery — a real file proves that directly.
# ---------------------------------------------------------------------------


def test_load_config_explicit_path_not_found(capsys):
    config = load_config("/nonexistent/path/to/bumpcalver.toml")

    assert config == {}
    captured = capsys.readouterr()
    assert "Config file not found: /nonexistent/path/to/bumpcalver.toml" in captured.err


def test_load_config_explicit_path_flat_style_arbitrary_filename(tmp_path):
    # Not named "bumpcalver.toml" or "pyproject.toml" at all — proves the
    # nested-vs-flat decision is based on the basename being literally
    # "pyproject.toml", not on some other heuristic, and that any other
    # filename (however named) is treated as flat.
    config_file = tmp_path / "myproject-versions.toml"
    config_file.write_text(
        'version_format = "{current_date}.{build_count:03}"\n'
        'timezone = "UTC"\n\n'
        "[[file]]\n"
        'path = "src/__init__.py"\n'
        'file_type = "python"\n'
        'variable = "__version__"\n',
        encoding="utf-8",
    )

    config = load_config(str(config_file))

    assert config["version_format"] == "{current_date}.{build_count:03}"
    assert config["timezone"] == "UTC"
    assert config["file_configs"] == [
        {"path": "src/__init__.py", "file_type": "python", "variable": "__version__"}
    ]


def test_load_config_explicit_path_pyproject_toml_elsewhere_is_nested(tmp_path):
    # An explicit --config-file pointing at a pyproject.toml in some other
    # directory must still be parsed as nested under [tool.bumpcalver],
    # even though it's not this repo's own pyproject.toml.
    config_file = tmp_path / "other-project" / "pyproject.toml"
    config_file.parent.mkdir()
    config_file.write_text(
        "[tool.bumpcalver]\n"
        'version_format = "{current_date}-{build_count:03}"\n'
        'timezone = "Europe/London"\n'
        "file = []\n",
        encoding="utf-8",
    )

    config = load_config(str(config_file))

    assert config["version_format"] == "{current_date}-{build_count:03}"
    assert config["timezone"] == "Europe/London"


def test_load_config_explicit_path_bypasses_cwd_auto_discovery(tmp_path, monkeypatch):
    # Even if a pyproject.toml exists in the cwd, an explicit config_path
    # must be used instead — never silently fall back to auto-discovery.
    # os.path.exists is stubbed to say "pyproject.toml" exists (in the cwd)
    # *and* the real explicit file exists, but nothing else — if the code
    # under test ever fell back to cwd auto-discovery it would load the
    # wrong (pyproject.toml-shaped) content instead of "explicit-format".
    config_file = tmp_path / "explicit.toml"
    config_file.write_text('version_format = "explicit-format"\nfile = []\n', encoding="utf-8")

    real_exists = os.path.exists
    monkeypatch.setattr(
        os.path,
        "exists",
        lambda x: x == "pyproject.toml" or real_exists(x),
    )

    config = load_config(str(config_file))

    assert config["version_format"] == "explicit-format"
