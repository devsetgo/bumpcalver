# tests/test_cli.py

import logging
import os
import subprocess
import tempfile
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
import toml
from bumpcalver._file_types import (
    read_version_from_makefile,
    read_version_from_python_file,
    read_version_from_toml_file,
    update_dockerfile,
    update_makefile,
    update_python_file,
    update_toml_file,
)
from click.testing import CliRunner
from src.bumpcalver._date_functions import (
    get_build_version,
    get_current_date,
    get_current_datetime_version,
    parse_version,
)
from src.bumpcalver.cli import create_git_tag, load_config, main, update_version_in_files

# Configure logging
logging.basicConfig(level=logging.DEBUG)


# Test get_current_date()
def test_get_current_date():
    tz = "UTC"
    expected_date = datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%d")
    assert get_current_date(timezone=tz) == expected_date


# Test get_current_date() with invalid timezone
def test_get_current_date_invalid_timezone(capfd):
    tz = "Invalid/Timezone"
    default_tz = "America/New_York"
    expected_date = datetime.now(ZoneInfo(default_tz)).strftime("%Y-%m-%d")
    assert get_current_date(timezone=tz) == expected_date
    out, err = capfd.readouterr()
    assert f"Unknown timezone '{tz}'. Using default '{default_tz}'." in out


# Test get_current_datetime_version()
def test_get_current_datetime_version():
    tz = "UTC"
    expected_datetime = datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%d-%H%M")
    assert get_current_datetime_version(timezone=tz) == expected_datetime


# Test get_current_datetime_version() with invalid timezone
def test_get_current_datetime_version_invalid_timezone(capfd):
    tz = "Invalid/Timezone"
    default_tz = "America/New_York"
    expected_datetime = datetime.now(ZoneInfo(default_tz)).strftime("%Y-%m-%d-%H%M")
    assert get_current_datetime_version(timezone=tz) == expected_datetime
    out, err = capfd.readouterr()
    assert f"Unknown timezone '{tz}'. Using default '{default_tz}'." in out


# Test parse_version()
def test_parse_version():
    version = "2023-10-05-001"
    last_date, last_count = parse_version(version)
    assert last_date == "2023-10-05"
    assert last_count == 1

    version = "2023-10-05-005-beta"
    last_date, last_count = parse_version(version)
    assert last_date == "2023-10-05"
    assert last_count == 5

    version = "2023-10-05"
    last_date, last_count = parse_version(version)
    assert last_date == "2023-10-05"
    assert last_count == 0

    version = "invalid-version"
    last_date, last_count = parse_version(version)
    assert last_date is None
    assert last_count is None


# Test read_version_from_python_file()
def test_read_version_from_python_file():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "2023-10-05-001"\n')
        temp_file_path = temp_file.name

    version = read_version_from_python_file(temp_file_path, "__version__")
    assert version == "2023-10-05-001"

    os.remove(temp_file_path)


# Test read_version_from_python_file() with missing variable
def test_read_version_from_python_file_missing_variable():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('version = "2023-10-05-001"\n')
        temp_file_path = temp_file.name

    version = read_version_from_python_file(temp_file_path, "__version__")
    assert version is None

    os.remove(temp_file_path)


# Test get_build_version()
def test_get_build_version():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "2023-10-05-001"\n')
        temp_file_path = temp_file.name

    file_config = {
        "path": temp_file_path,
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    # Mock current date to match the date in the temp file
    with mock.patch(
        "src.bumpcalver._date_functions.get_current_date", return_value="2023-10-05"
    ):
        new_version = get_build_version(file_config, version_format, timezone=tz)
        assert new_version == "2023-10-05-002"

    os.remove(temp_file_path)


# Test get_build_version() with invalid build count
def test_get_build_version_invalid_build_count(caplog):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "2023-10-05-abc"\n')
        temp_file_path = temp_file.name

    file_config = {
        "path": temp_file_path,
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    with mock.patch(
        "src.bumpcalver._date_functions.get_current_date", return_value="2023-10-05"
    ):
        with caplog.at_level(logging.WARNING):
            new_version = get_build_version(file_config, version_format, timezone=tz)
            assert new_version == "2023-10-05-001"
            # assert (
            #     f"Warning: Invalid build count 'abc' in {temp_file_path}. Resetting to 1."
            #     in caplog.text
            # )

    os.remove(temp_file_path)


# Test get_build_version() with missing file
def test_get_build_version_missing_file(caplog):
    file_config = {
        "path": "non_existent_file.txt",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    with mock.patch(
        "src.bumpcalver._date_functions.get_current_date", return_value="2023-09-30"
    ):
        with caplog.at_level(logging.WARNING):
            new_version = get_build_version(file_config, version_format, timezone=tz)
            assert new_version == "2023-09-30-001"
            assert (
                "Could not read version from non_existent_file.txt. Starting new versioning."
                in caplog.text
            )


# Test get_build_version() when version does not match expected format
def test_get_build_version_version_mismatch(capfd):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "v0.1.0"\n')
        temp_file_path = temp_file.name

    file_config = {
        "path": temp_file_path,
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    with mock.patch(
        "src.bumpcalver._date_functions.get_current_date", return_value="2023-10-05"
    ):
        new_version = get_build_version(file_config, version_format, timezone=tz)
        assert new_version == "2023-10-05-001"
        out, err = capfd.readouterr()
        assert "Version 'v0.1.0' does not match expected format." in out

    os.remove(temp_file_path)


# Test get_build_version() when unsupported file_type is specified
def test_get_build_version_unsupported_file_type(caplog):
    file_config = {
        "path": "version.txt",
        "file_type": "unsupported_type",
        "variable": "version",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    with mock.patch(
        "src.bumpcalver._date_functions.get_current_date", return_value="2023-10-05"
    ):
        with caplog.at_level(logging.WARNING):
            new_version = get_build_version(file_config, version_format, timezone=tz)
            assert (
                new_version == "2023-10-05-001"
            )  # Assuming today's date is 2023-10-05
            assert (
                "Unsupported file type 'unsupported_type' for build version."
                in caplog.text
            )


# Test update_python_file()
def test_update_python_file():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "0.1.0"\n')
        temp_file_path = temp_file.name

    success = update_python_file(temp_file_path, "__version__", "2023-10-05-001")
    assert success

    with open(temp_file_path, "r") as f:
        content = f.read()
        assert content.strip() == '__version__ = "2023-10-05-001"'

    os.remove(temp_file_path)


# Test update_toml_file()
def test_update_toml_file():
    temp_file_content = """
[project]
name = "example"
version = "0.1.0"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    success = update_toml_file(temp_file_path, "project", "version", "2023-10-05-001")
    assert success

    with open(temp_file_path, "r") as f:
        data = toml.load(f)
        assert data["project"]["version"] == "2023-10-05-001"

    os.remove(temp_file_path)


# Test update_makefile()
def test_update_makefile():
    temp_file_content = """
VERSION = 0.1.0
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    success = update_makefile(temp_file_path, "VERSION", "2023-10-05-001")
    assert success

    with open(temp_file_path, "r") as f:
        content = f.read()
        assert "VERSION = 2023-10-05-001" in content

    os.remove(temp_file_path)


# Test update_dockerfile()
def test_update_dockerfile():
    temp_file_content = """
FROM python:3.9
LABEL version="0.1.0"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    success = update_dockerfile(temp_file_path, "2023-10-05-001")
    assert success

    with open(temp_file_path, "r") as f:
        content = f.read()
        assert 'LABEL version="2023-10-05-001"' in content

    os.remove(temp_file_path)


# Test update_version_in_files()
def test_update_version_in_files():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "0.1.0"\n')
        temp_file_path = temp_file.name

    new_version = "2023-10-05-001"
    file_configs = [
        {
            "path": temp_file_path,
            "file_type": "python",
            "variable": "__version__",
        }
    ]

    updated_files = update_version_in_files(new_version, file_configs)

    with open(temp_file_path, "r") as f:
        content = f.read()
        assert content.strip() == f'__version__ = "{new_version}"'

    assert os.path.relpath(temp_file_path) in updated_files

    os.remove(temp_file_path)


# Test update_version_in_files() with missing file_type
def test_update_version_in_files_missing_file_type(capfd):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "0.1.0"\n')
        temp_file_path = temp_file.name

    new_version = "2023-10-05-001"
    file_configs = [
        {
            "path": temp_file_path,
            "variable": "__version__",
        }
    ]

    updated_files = update_version_in_files(new_version, file_configs)
    assert updated_files == []
    out, err = capfd.readouterr()
    assert f"No file_type specified for {temp_file_path}" in out

    os.remove(temp_file_path)


# Test update_version_in_files() with unsupported file_type
def test_update_version_in_files_unsupported_file_type(capfd):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('version = "0.1.0"\n')
        temp_file_path = temp_file.name

    new_version = "2023-10-05-001"
    file_configs = [
        {
            "path": temp_file_path,
            "file_type": "unsupported",
            "variable": "version",
        }
    ]

    updated_files = update_version_in_files(new_version, file_configs)
    assert updated_files == []
    out, err = capfd.readouterr()
    assert f"Unsupported file type 'unsupported' for {temp_file_path}" in out

    os.remove(temp_file_path)


# Test load_config()
def test_load_config():
    # Create a temporary pyproject.toml
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(
            """
[tool.bumpcalver]
version_format = "{current_date}-{build_count:03}"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "version.py"
file_type = "python"
variable = "__version__"
"""
        )
        temp_file_path = temp_file.name

    # Mock os.path.exists to return True when checking for pyproject.toml
    with mock.patch("os.path.exists", return_value=True):
        # Mock open to read from our temp_file
        with mock.patch(
            "builtins.open", new=mock.mock_open(read_data=open(temp_file_path).read())
        ):
            config = load_config()
            assert config["version_format"] == "{current_date}-{build_count:03}"
            assert config["timezone"] == "UTC"
            assert config["git_tag"] is True
            assert config["auto_commit"] is True
            assert len(config["file_configs"]) == 1
            assert config["file_configs"][0]["path"] == "version.py"
            assert config["file_configs"][0]["file_type"] == "python"
            assert config["file_configs"][0]["variable"] == "__version__"

    os.remove(temp_file_path)


# Test load_config() with missing pyproject.toml
def test_load_config_missing_pyproject():
    # Mock os.path.exists to return False when checking for pyproject.toml
    with mock.patch("os.path.exists", return_value=False):
        config = load_config()
        assert config == {}


# Test create_git_tag()
def test_create_git_tag():
    version = "2023-10-05-001"
    files_to_commit = ["file1.txt", "file2.txt"]
    auto_commit = True

    with mock.patch("subprocess.run") as mock_run:
        create_git_tag(version, files_to_commit, auto_commit)

        # Check that subprocess.run was called with git commands
        calls = [
            mock.call(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ),
            mock.call(["git", "add"] + files_to_commit, check=True),
            mock.call(
                ["git", "commit", "-m", f"Bump version to {version}"], check=True
            ),
            mock.call(["git", "tag", version], check=True),
        ]
        mock_run.assert_has_calls(calls)


# Test main() function with no files specified
def test_main_no_files_specified():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create an empty pyproject.toml
        with open("pyproject.toml", "w") as f:
            f.write(
                """
[tool.bumpcalver]
version_format = "{current_date}-{build_count:03}"
timezone = "UTC"
git_tag = true
auto_commit = true
"""
            )
        result = runner.invoke(main, ["--build"])
        assert result.exit_code == 0
        assert "No files specified in the configuration." in result.output


# Test main() function with various options
@pytest.mark.parametrize(
    "options, expected_version_prefix",
    [
        (["--build"], ""),  # Standard build
        (["--build", "--beta"], "-beta"),  # Beta versioning
        (["--build", "--timezone", "UTC"], ""),  # Specified timezone
        (["--build", "--git-tag"], ""),  # Force git tag
        (["--build", "--no-git-tag"], ""),  # Disable git tag
        (["--build", "--auto-commit"], ""),  # Force auto-commit
        (["--build", "--no-auto-commit"], ""),  # Disable auto-commit
    ],
)
def test_main_with_options_first(options, expected_version_prefix):
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create necessary files
        with open("pyproject.toml", "w") as f:
            f.write(
                """
[tool.bumpcalver]
version_format = "{current_date}-{build_count:03}"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "version.py"
file_type = "python"
variable = "__version__"
"""
            )
        with open("version.py", "w") as f:
            f.write('__version__ = "0.1.0"\n')

        with mock.patch("src.bumpcalver.cli.create_git_tag") as mock_create_git_tag:
            result = runner.invoke(main, options)
            assert result.exit_code == 0
            assert "Updated version to " in result.output

            # Verify that the version was updated
            with open("version.py", "r") as f:
                content = f.read()
                expected_version = f'__version__ = "{expected_version_prefix}'
                assert expected_version in content

            # Check if create_git_tag was called based on options
            if "--no-git-tag" in options:
                mock_create_git_tag.assert_not_called()
            else:
                mock_create_git_tag.assert_called_once()


# Test main() function when pyproject.toml is missing
def test_main_pyproject_missing():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["--build"])
        assert result.exit_code == 0
        assert "No files specified in the configuration." in result.output


# Test main() function with malformed pyproject.toml
def test_main_pyproject_malformed():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("pyproject.toml", "w") as f:
            f.write(
                """
[tool.bumpcalver
version_format = "{current_date}-{build_count:03"
"""
            )
        result = runner.invoke(main, ["--build"])
        assert result.exit_code == 1
        assert "Error parsing pyproject.toml:" in result.output


# Test main() function with invalid timezone
def test_main_invalid_timezone():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create pyproject.toml with invalid timezone
        with open("pyproject.toml", "w") as f:
            f.write(
                """
[tool.bumpcalver]
version_format = "{current_date}-{build_count:03}"
timezone = "Invalid/Timezone"

[[tool.bumpcalver.file]]
path = "version.py"
file_type = "python"
variable = "__version__"
"""
            )
        with open("version.py", "w") as f:
            f.write('__version__ = "0.1.0"\n')

        result = runner.invoke(main, ["--build"])
        assert result.exit_code == 0
        assert "Unknown timezone" in result.output
        assert "Updated version to " in result.output


# Test main() function with beta versioning
def test_main_beta_versioning():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("pyproject.toml", "w") as f:
            f.write(
                """
                [tool.bumpcalver]
                version_format = "{current_date}-{build_count:03}"
                file_configs = []
                timezone = "UTC"
                git_tag = false
                auto_commit = false
                """
            )
        result = runner.invoke(main, ["--build", "--beta"])
        assert result.exit_code == 0
        assert "-beta" in result.output


# Test get_build_version() when the last date is not the current date
def test_get_build_version_new_date():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('__version__ = "2023-10-04-001"\n')
        temp_file_path = temp_file.name

    file_config = {
        "path": temp_file_path,
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    # Mock current date to a different date
    with mock.patch(
        "src.bumpcalver._date_functions.get_current_date", return_value="2023-10-05"
    ):
        new_version = get_build_version(file_config, version_format, timezone=tz)
        assert new_version == "2023-10-05-001"

    os.remove(temp_file_path)


# Test update_python_file() when the variable is not found
def test_update_python_file_variable_not_found():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write('version = "0.1.0"\n')
        temp_file_path = temp_file.name

    success = update_python_file(temp_file_path, "__version__", "2023-10-05-001")
    assert not success

    os.remove(temp_file_path)


# Test update_toml_file() when the variable is not found
def test_update_toml_file_variable_not_found():
    temp_file_content = """
[project]
name = "example"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    success = update_toml_file(temp_file_path, "project", "version", "2023-10-05-001")
    assert not success

    os.remove(temp_file_path)


# Test update_makefile() when the variable is not found
def test_update_makefile_variable_not_found():
    temp_file_content = """
VERSION = 0.1.0
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    success = update_makefile(temp_file_path, "NON_EXISTENT_VARIABLE", "2023-10-05-001")
    assert not success

    os.remove(temp_file_path)


# Test update_dockerfile() when the variable is not found
def test_update_dockerfile_variable_not_found():
    temp_file_content = """
FROM python:3.9
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    success = update_dockerfile(temp_file_path, "2023-10-05-001")
    assert not success

    os.remove(temp_file_path)


# Test create_git_tag() with auto-commit
def test_create_git_tag_with_auto_commit():
    with mock.patch("subprocess.run") as mock_run:
        create_git_tag("v1.0.0", ["file1.txt"], True)
        mock_run.assert_any_call(["git", "add", "file1.txt"], check=True)
        mock_run.assert_any_call(
            ["git", "commit", "-m", "Bump version to v1.0.0"], check=True
        )
        mock_run.assert_any_call(["git", "tag", "v1.0.0"], check=True)


# Test main() function with various options
@pytest.mark.parametrize(
    "options, expected_version_suffix",
    [
        (["--build"], ""),
        (["--build", "--beta"], "-beta"),
        (["--build", "--timezone", "UTC"], ""),
        (["--build", "--git-tag"], ""),
        (["--build", "--no-git-tag"], ""),
        (["--build", "--auto-commit"], ""),
        (["--build", "--no-auto-commit"], ""),
    ],
)
def test_main_with_options(options, expected_version_suffix):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("pyproject.toml", "w") as f:
            f.write(
                """
                [tool.bumpcalver]
                version_format = "{current_date}-{build_count:03}"
                file_configs = []
                timezone = "UTC"
                git_tag = false
                auto_commit = false
                """
            )
        result = runner.invoke(main, options)
        assert result.exit_code == 0
        assert expected_version_suffix in result.output


# Test read_version_from_toml_file() with valid section and variable
def test_read_version_from_toml_file():
    temp_file_content = """
[project]
name = "example"
version = "0.1.0"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_toml_file(temp_file_path, "project", "version")
    assert version == "0.1.0"

    os.remove(temp_file_path)


# Test read_version_from_toml_file() with nested section
def test_read_version_from_toml_file_nested_section():
    temp_file_content = """
[tool.bumpcalver]
version = "0.1.0"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_toml_file(temp_file_path, "tool.bumpcalver", "version")
    assert version == "0.1.0"

    os.remove(temp_file_path)


# Test read_version_from_toml_file() with missing variable
def test_read_version_from_toml_file_missing_variable():
    temp_file_content = """
[project]
name = "example"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_toml_file(temp_file_path, "project", "version")
    assert version is None

    os.remove(temp_file_path)


# Test read_version_from_toml_file() with missing section
def test_read_version_from_toml_file_missing_section():
    temp_file_content = """
[project]
name = "example"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_toml_file(temp_file_path, "nonexistent", "version")
    assert version is None

    os.remove(temp_file_path)


# Test read_version_from_toml_file() with invalid TOML content
def test_read_version_from_toml_file_invalid_toml():
    temp_file_content = """
[project
name = "example"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_toml_file(temp_file_path, "project", "version")
    assert version is None

    os.remove(temp_file_path)


# Test read_version_from_makefile() with valid variable
def test_read_version_from_makefile():
    temp_file_content = """
VERSION = 0.1.0
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_makefile(temp_file_path, "VERSION")
    assert version == "0.1.0"

    os.remove(temp_file_path)


# Test read_version_from_makefile() with missing variable
def test_read_version_from_makefile_missing_variable():
    temp_file_content = """
VERSION = 0.1.0
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_makefile(temp_file_path, "NON_EXISTENT_VARIABLE")
    assert version is None

    os.remove(temp_file_path)


# Test read_version_from_makefile() with invalid Makefile content
def test_read_version_from_makefile_invalid_content():
    temp_file_content = """
VERSION 0.1.0
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    version = read_version_from_makefile(temp_file_path, "VERSION")
    assert version is None

    os.remove(temp_file_path)


# Test create_git_tag() with auto-commit and error during Git operations
def test_create_git_tag_git_operations_error(capfd):
    with mock.patch("subprocess.run") as mock_run:
        # Simulate successful git rev-parse
        mock_run.side_effect = [None, subprocess.CalledProcessError(1, "git")]
        create_git_tag("v1.0.0", ["file1.txt"], True)
        out, err = capfd.readouterr()
        assert "Error during Git operations:" in out


# Test create_git_tag() when not in a Git repository
def test_create_git_tag_not_in_git_repo(capfd):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        create_git_tag("v1.0.0", [], False)
        out, err = capfd.readouterr()
        assert "Not a Git repository. Skipping Git tagging." in out


# Test update_dockerfile() when an exception is raised
def test_update_dockerfile_exception():
    temp_file_content = """
FROM python:3.9
LABEL version="0.1.0"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    new_version = "2023-10-05-001"

    # Mock the open function to raise an exception
    with mock.patch("builtins.open", mock.mock_open()) as mock_open:
        mock_open.side_effect = Exception("Mocked exception")
        success = update_dockerfile(temp_file_path, new_version)
        assert not success

    os.remove(temp_file_path)


# Test update_makefile() when an exception is raised
def test_update_makefile_exception():
    temp_file_content = """
VERSION = 0.1.0
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    new_version = "2023-10-05-001"

    # Mock the open function to raise an exception
    with mock.patch("builtins.open", mock.mock_open()) as mock_open:
        mock_open.side_effect = Exception("Mocked exception")
        success = update_makefile(temp_file_path, "VERSION", new_version)
        assert not success

    os.remove(temp_file_path)


# Test update_toml_file() when an exception is raised
def test_update_toml_file_exception():
    temp_file_content = """
[project]
name = "example"
version = "0.1.0"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    new_version = "2023-10-05-001"

    # Mock the open function to raise an exception
    with mock.patch("builtins.open", mock.mock_open()) as mock_open:
        mock_open.side_effect = Exception("Mocked exception")
        success = update_toml_file(temp_file_path, "project", "version", new_version)
        assert not success

    os.remove(temp_file_path)


# Test update_python_file() when an exception is raised
def test_update_python_file_exception():
    temp_file_content = """
__version__ = "0.1.0"
"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        temp_file.write(temp_file_content)
        temp_file_path = temp_file.name

    new_version = "2023-10-05-001"

    # Mock the open function to raise an exception
    with mock.patch("builtins.open", mock.mock_open()) as mock_open:
        mock_open.side_effect = Exception("Mocked exception")
        success = update_python_file(temp_file_path, "__version__", new_version)
        assert not success

    os.remove(temp_file_path)


# Test get_build_version() when an exception is raised
def test_get_build_version_exception():
    file_config = {
        "path": "non_existent_file.txt",
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    # Mock the read_version_from_python_file function to raise an exception
    with mock.patch(
        "src.bumpcalver._file_types.read_version_from_python_file"
    ) as mock_read:
        mock_read.side_effect = Exception("Mocked exception")
        with mock.patch(
            "src.bumpcalver._date_functions.get_current_date", return_value="2023-10-05"
        ):
            version = get_build_version(file_config, version_format, timezone=tz)
            assert version == "2023-10-05-001"


# Test get_build_version() when a ValueError is raised
def test_get_build_version_value_error():
    file_config = {
        "path": "non_existent_file.txt",
        "file_type": "python",
        "variable": "__version__",
    }
    version_format = "{current_date}-{build_count:03}"
    tz = "UTC"

    # Mock the read_version_from_python_file function to raise a ValueError
    with mock.patch(
        "src.bumpcalver._file_types.read_version_from_python_file"
    ) as mock_read:
        mock_read.side_effect = ValueError("Mocked ValueError")
        with mock.patch(
            "src.bumpcalver._date_functions.get_current_date", return_value="2023-10-05"
        ):
            version = get_build_version(file_config, version_format, timezone=tz)
            assert version == "2023-10-05-001"


# Test read_version_from_makefile() when an exception is raised
def test_read_version_from_makefile_exception():
    file_path = "non_existent_file.txt"
    variable = "VERSION"

    # Mock the open function to raise an exception
    with mock.patch("builtins.open", mock.mock_open()) as mock_open:
        mock_open.side_effect = Exception("Mocked exception")
        version = read_version_from_makefile(file_path, variable)
        assert version is None


# Test read_version_from_python_file() when an exception is raised
def test_read_version_from_python_file_exception():
    file_path = "non_existent_file.txt"
    variable = "__version__"

    # Mock the open function to raise an exception
    with mock.patch("builtins.open", mock.mock_open()) as mock_open:
        mock_open.side_effect = Exception("Mocked exception")
        version = read_version_from_python_file(file_path, variable)
        assert version is None
