# tests/test_utils.py

import os
import re
from unittest import mock

from src.bumpcalver.utils import (
    get_build_version,
    get_current_date,
    get_current_datetime_version,
    parse_dot_path,
    parse_version,
)


def test_parse_dot_path_with_slash():
    path = "some/path/file.py"
    result = parse_dot_path(path, "python")
    assert result == path


def test_parse_dot_path_with_backslash():
    path = "some\\path\\file.py"
    result = parse_dot_path(path, "python")
    assert result == path


def test_parse_dot_path_with_absolute_path():
    path = "/absolute/path/file.py"
    result = parse_dot_path(path, "python")
    assert result == path


def test_parse_dot_path_python_module():
    path = "module.submodule.file"
    expected = os.path.join("module", "submodule", "file.py")
    result = parse_dot_path(path, "python")
    assert result == expected


def test_parse_dot_path_python_with_py_extension():
    path = "module.py"
    result = parse_dot_path(path, "python")
    assert result == path


def test_parse_dot_path_non_python_file_type():
    path = "some.path.file"
    result = parse_dot_path(path, "json")
    assert result == path


def test_parse_version_with_date_and_count():
    version = "2023-10-11-2"
    expected = ("2023-10-11", 2)
    result = parse_version(version)
    assert result == expected


def test_parse_version_with_date_only():
    version = "2023-10-11"
    expected = ("2023-10-11", 0)
    result = parse_version(version)
    assert result == expected


def test_parse_version_invalid_format(capsys):
    version = "v1.0.0"
    result = parse_version(version)
    assert result is None
    captured = capsys.readouterr()
    assert "Version 'v1.0.0' does not match expected format 'YYYY-MM-DD' or 'YYYY-MM-DD-XXX'." in captured.out


def test_parse_version_with_quarter_format():
    """Test parsing version with custom quarter format."""
    version = "25.Q4.001"
    version_format = "{current_date}.{build_count:03}"
    date_format = "%y.Q%q"
    expected = ("25.Q4", 1)
    result = parse_version(version, version_format, date_format)
    assert result == expected


def test_parse_version_with_quarter_format_and_beta():
    """Test parsing version with custom quarter format and beta suffix."""
    version = "25.Q4.001.beta"
    version_format = "{current_date}.{build_count:03}"
    date_format = "%y.Q%q"
    expected = ("25.Q4", 1)
    result = parse_version(version, version_format, date_format)
    assert result == expected


def test_parse_version_with_custom_format_no_count():
    """Test parsing version with custom format but no build count."""
    version = "25.Q4"
    version_format = "{current_date}"
    date_format = "%y.Q%q"
    expected = ("25.Q4", 0)
    result = parse_version(version, version_format, date_format)
    assert result == expected


def test_parse_version_dot_separated_non_numeric_build_count(capsys):
    version = "24.12.xyz"
    version_format = "{current_date}.{build_count:03}"
    date_format = "%y.%m"

    result = parse_version(version, version_format, date_format)
    assert result is None

    captured = capsys.readouterr()
    assert "Failed" not in captured.out
    assert "does not match format" in captured.out


def test_parse_version_dynamic_parsing_exception_is_handled(capsys):
    # Intentionally pass a non-string version_format to force a TypeError inside
    # the dynamic parsing helper. This should be caught and logged by parse_version.
    version = "24.12.001"
    result = parse_version(version, object(), "%y.%m")
    assert result is None

    captured = capsys.readouterr()
    assert "Dynamic version parsing failed for '24.12.001':" in captured.out


def test_get_current_date_valid_timezone():
    result = get_current_date("America/New_York")
    assert result is not None
    assert re.match(r"\d{4}\.\d{2}\.\d{2}", result)


def test_get_current_date_invalid_timezone():
    result = get_current_date("Invalid/Timezone")
    assert result is not None
    assert re.match(r"\d{4}\.\d{2}\.\d{2}", result)


def test_get_current_datetime_version_valid_timezone():
    result = get_current_datetime_version("America/New_York")
    assert result is not None
    assert re.match(r"\d{4}\.\d{2}\.\d{2}", result)


def test_get_current_datetime_version_invalid_timezone():
    result = get_current_datetime_version("Invalid/Timezone")
    assert result is not None
    assert re.match(r"\d{4}\.\d{2}\.\d{2}", result)


def test_get_build_version_version_exists_today(monkeypatch):
    current_date = "2023-10-11"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_current_datetime_version", lambda tz, df: current_date
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "2023-10-11-1"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_version_handler", lambda ft: mock_handler
    )

    file_config = {
        "path": "dummy_path",
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count}"
    result = get_build_version(file_config, version_format, "UTC", "%Y-%m-%d")
    assert result == "2023-10-11-2"


def test_get_build_version_version_exists_not_today(monkeypatch):
    current_date = "2023-10-11"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_current_datetime_version", lambda tz, df: current_date
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "2023-10-10-5"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_version_handler", lambda ft: mock_handler
    )

    file_config = {
        "path": "dummy_path",
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count}"
    result = get_build_version(file_config, version_format, "UTC", "%Y-%m-%d")
    assert result == "2023-10-11-1"


def test_get_build_version_version_not_found(monkeypatch, capsys):
    current_date = "2023-10-11"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_current_datetime_version", lambda tz, df: current_date
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = None
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_version_handler", lambda ft: mock_handler
    )

    file_config = {
        "path": "dummy_path",
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count}"
    result = get_build_version(file_config, version_format, "UTC", "%Y-%m-%d")
    assert result == "2023-10-11-1"

    captured = capsys.readouterr()
    assert (
        "File 'dummy_path': Could not read version. Starting new versioning with format 'YYYY-MM-DD-XXX'."
        in captured.out
    )


def test_get_build_version_invalid_version_format(monkeypatch, capsys):
    current_date = "2023-10-11"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_current_datetime_version", lambda tz, df: current_date
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "v1.0.0"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_version_handler", lambda ft: mock_handler
    )

    file_config = {
        "path": "dummy_path",
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count}"
    result = get_build_version(file_config, version_format, "UTC", "%Y-%m-%d")
    assert result == "2023-10-11-1"

    captured = capsys.readouterr()
    assert "File 'dummy_path': Version 'v1.0.0' does not match expected format. Expected format: '{current_date}-{build_count}' with date format: '%Y-%m-%d'." in captured.out


def test_get_build_version_exception_during_read(monkeypatch, capsys):
    current_date = "2023-10-11"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_current_datetime_version", lambda tz, df: current_date
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.side_effect = Exception("Read error")
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_version_handler", lambda ft: mock_handler
    )

    file_config = {
        "path": "dummy_path",
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count}"
    result = get_build_version(file_config, version_format, "UTC", "%Y-%m-%d")
    assert result == "2023-10-11-1"

    captured = capsys.readouterr()
    assert "File 'dummy_path': Error reading version - Read error. Starting new versioning with format 'YYYY-MM-DD-XXX'." in captured.out


def test_get_build_version_with_directive(monkeypatch):
    current_date = "2023-10-11"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_current_datetime_version", lambda tz, df: current_date
    )

    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "2023-10-11-1"
    monkeypatch.setattr(
        "src.bumpcalver.utils.get_version_handler", lambda ft: mock_handler
    )

    file_config = {
        "path": "dummy_path",
        "file_type": "dockerfile",
        "variable": "VERSION",
        "directive": "ARG",
    }
    version_format = "{current_date}-{build_count}"
    result = get_build_version(file_config, version_format, "UTC", "%Y-%m-%d")
    assert result == "2023-10-11-2"

    mock_handler.read_version.assert_called_with(
        "dummy_path", "VERSION", directive="ARG"
    )
