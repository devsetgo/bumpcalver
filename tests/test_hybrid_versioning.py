"""Tests for hybrid semantic+calendar versioning support."""

import os
import tempfile
from unittest import mock

import pytest
from click.testing import CliRunner

from src.bumpcalver.cli import main
from src.bumpcalver.utils import (
    _date_format_to_regex,
    _is_hybrid_format,
    _parse_hybrid_version,
    get_build_version,
    parse_version,
    update_semantic_in_config,
)


# ---------------------------------------------------------------------------
# _is_hybrid_format
# ---------------------------------------------------------------------------

class TestIsHybridFormat:
    def test_major_placeholder(self):
        assert _is_hybrid_format("{major}.{minor}-{current_date}.{build_count}") is True

    def test_minor_placeholder(self):
        assert _is_hybrid_format("{minor}-{current_date}.{build_count}") is True

    def test_patch_placeholder(self):
        assert _is_hybrid_format("{patch}-{current_date}.{build_count}") is True

    def test_all_placeholders(self):
        assert _is_hybrid_format("{major}.{minor}.{patch}-{current_date}.{build_count}") is True

    def test_pure_calver_is_not_hybrid(self):
        assert _is_hybrid_format("{current_date}.{build_count:03}") is False

    def test_date_only_is_not_hybrid(self):
        assert _is_hybrid_format("{current_date}") is False

    def test_empty_format_is_not_hybrid(self):
        assert _is_hybrid_format("") is False


# ---------------------------------------------------------------------------
# _date_format_to_regex
# ---------------------------------------------------------------------------

class TestDateFormatToRegex:
    def test_yyyymmdd_compact(self):
        rx = _date_format_to_regex("%Y%m%d")
        assert rx == r"\d{4}\d{2}\d{2}"

    def test_yy_dot_mm_dot_dd(self):
        rx = _date_format_to_regex("%y.%m.%d")
        assert rx == r"\d{2}\.\d{2}\.\d{2}"

    def test_yyyy_dot_mm_dot_dd(self):
        rx = _date_format_to_regex("%Y.%m.%d")
        assert rx == r"\d{4}\.\d{2}\.\d{2}"

    def test_quarter_format(self):
        rx = _date_format_to_regex("%y.Q%q")
        assert rx == r"\d{2}\.Q\d"

    def test_compact_yymmdd(self):
        rx = _date_format_to_regex("%y%m%d")
        assert rx == r"\d{2}\d{2}\d{2}"

    def test_day_of_year(self):
        rx = _date_format_to_regex("%Y.%j")
        assert rx == r"\d{4}\.\d{3}"


# ---------------------------------------------------------------------------
# _parse_hybrid_version — success cases
# ---------------------------------------------------------------------------

class TestParseHybridVersionSuccess:
    def test_major_minor_yyyymmdd_dot_count(self):
        result = _parse_hybrid_version(
            "1.0-20260518.1",
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result == ("20260518", 1)

    def test_major_minor_patch_yyyymmdd_dot_count_padded(self):
        result = _parse_hybrid_version(
            "1.0.0-20260518.001",
            "{major}.{minor}.{patch}-{current_date}.{build_count:03}",
            "%Y%m%d",
        )
        assert result == ("20260518", 1)

    def test_major_minor_yyyymmdd_dash_count(self):
        result = _parse_hybrid_version(
            "2.3-20260518-01",
            "{major}.{minor}-{current_date}-{build_count:02}",
            "%Y%m%d",
        )
        assert result == ("20260518", 1)

    def test_major_minor_yyyy_dot_mm_dot_dd_dot_count(self):
        result = _parse_hybrid_version(
            "1.0-2026.05.18.001",
            "{major}.{minor}-{current_date}.{build_count:03}",
            "%Y.%m.%d",
        )
        assert result == ("2026.05.18", 1)

    def test_higher_build_count_incremented(self):
        result = _parse_hybrid_version(
            "1.0-20260518.7",
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result == ("20260518", 7)

    def test_quarter_format(self):
        result = _parse_hybrid_version(
            "1.0-26.Q2.5",
            "{major}.{minor}-{current_date}.{build_count}",
            "%y.Q%q",
        )
        assert result == ("26.Q2", 5)

    def test_major_minor_patch_all_present(self):
        result = _parse_hybrid_version(
            "2.3.4-20260518.10",
            "{major}.{minor}.{patch}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result == ("20260518", 10)

    def test_strips_beta_suffix(self):
        result = _parse_hybrid_version(
            "1.0-20260518.1.beta",
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result == ("20260518", 1)


# ---------------------------------------------------------------------------
# _parse_hybrid_version — failure cases
# ---------------------------------------------------------------------------

class TestParseHybridVersionFailure:
    def test_wrong_separator_returns_none(self):
        result = _parse_hybrid_version(
            "1.0_20260518.1",  # underscore instead of dash
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result is None

    def test_non_numeric_major_returns_none(self):
        result = _parse_hybrid_version(
            "X.0-20260518.1",
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result is None

    def test_date_wrong_length_returns_none(self):
        # date_format expects 8 digits, version has 6
        result = _parse_hybrid_version(
            "1.0-202605.1",
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result is None

    def test_completely_wrong_format_returns_none(self):
        result = _parse_hybrid_version(
            "not-a-version",
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result is None


# ---------------------------------------------------------------------------
# parse_version routing
# ---------------------------------------------------------------------------

class TestParseVersionRouting:
    def test_hybrid_format_routed_correctly(self):
        result = parse_version(
            "1.0-20260518.3",
            "{major}.{minor}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result == ("20260518", 3)

    def test_pure_calver_still_works(self):
        result = parse_version(
            "26.05.18.001",
            "{current_date}.{build_count:03}",
            "%y.%m.%d",
        )
        assert result == ("26.05.18", 1)

    def test_legacy_calver_still_works(self):
        result = parse_version("2024-12-07-001")
        assert result == ("2024-12-07", 1)

    def test_hybrid_with_patch(self):
        result = parse_version(
            "2.3.4-20260518.10",
            "{major}.{minor}.{patch}-{current_date}.{build_count}",
            "%Y%m%d",
        )
        assert result == ("20260518", 10)


# ---------------------------------------------------------------------------
# get_build_version with hybrid format
# ---------------------------------------------------------------------------

class TestGetBuildVersionHybrid:
    def test_same_day_increments(self, tmp_path):
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text('[project]\nversion = "1.0-20260518.3"\n')
        version_format = "{major}.{minor}-{current_date}.{build_count}"
        date_format = "%Y%m%d"
        file_config = {"path": str(toml_file), "file_type": "toml", "variable": "project.version"}

        with mock.patch("src.bumpcalver.utils.get_current_datetime_version", return_value="20260518"):
            result = get_build_version(
                file_config, version_format, "UTC", date_format,
                major=1, minor=0, patch=0,
            )

        assert result == "1.0-20260518.4"

    def test_new_day_resets_count(self, tmp_path):
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text('[project]\nversion = "1.0-20260517.5"\n')
        version_format = "{major}.{minor}-{current_date}.{build_count}"
        date_format = "%Y%m%d"
        file_config = {"path": str(toml_file), "file_type": "toml", "variable": "project.version"}

        with mock.patch("src.bumpcalver.utils.get_current_datetime_version", return_value="20260518"):
            result = get_build_version(
                file_config, version_format, "UTC", date_format,
                major=1, minor=0, patch=0,
            )

        assert result == "1.0-20260518.1"

    def test_semantic_values_reflected_in_output(self, tmp_path):
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text('[project]\nversion = "1.0-20260518.1"\n')
        version_format = "{major}.{minor}.{patch}-{current_date}.{build_count}"
        date_format = "%Y%m%d"
        file_config = {"path": str(toml_file), "file_type": "toml", "variable": "project.version"}

        with mock.patch("src.bumpcalver.utils.get_current_datetime_version", return_value="20260518"):
            result = get_build_version(
                file_config, version_format, "UTC", date_format,
                major=2, minor=3, patch=4,
            )

        assert result.startswith("2.3.4-")

    def test_first_run_no_existing_version(self, tmp_path):
        toml_file = tmp_path / "pyproject.toml"
        toml_file.write_text('[project]\nversion = ""\n')
        version_format = "{major}.{minor}-{current_date}.{build_count}"
        date_format = "%Y%m%d"
        file_config = {"path": str(toml_file), "file_type": "toml", "variable": "project.version"}

        with mock.patch("src.bumpcalver.utils.get_current_datetime_version", return_value="20260518"):
            result = get_build_version(
                file_config, version_format, "UTC", date_format,
                major=1, minor=0, patch=0,
            )

        assert result == "1.0-20260518.1"


# ---------------------------------------------------------------------------
# load_config with major/minor/patch
# ---------------------------------------------------------------------------

class TestLoadConfigSemanticKeys:
    def test_reads_major_minor_patch_from_config(self):
        from src.bumpcalver.config import load_config
        toml_content = """
[tool.bumpcalver]
major = 2
minor = 3
patch = 4
version_format = "{major}.{minor}.{patch}-{current_date}.{build_count}"
date_format = "%Y%m%d"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "pyproject.toml")
            with open(config_path, "w") as f:
                f.write(toml_content)
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                config = load_config()
                assert config["major"] == 2
                assert config["minor"] == 3
                assert config["patch"] == 4
            finally:
                os.chdir(original_dir)

    def test_defaults_to_zero_when_absent(self):
        from src.bumpcalver.config import load_config
        toml_content = """
[tool.bumpcalver]
version_format = "{current_date}.{build_count:03}"
date_format = "%Y%m%d"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "pyproject.toml")
            with open(config_path, "w") as f:
                f.write(toml_content)
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                config = load_config()
                assert config["major"] == 0
                assert config["minor"] == 0
                assert config["patch"] == 0
            finally:
                os.chdir(original_dir)


# ---------------------------------------------------------------------------
# update_semantic_in_config
# ---------------------------------------------------------------------------

class TestUpdateSemanticInConfig:
    def test_updates_major_in_pyproject_toml(self):
        content = "[tool.bumpcalver]\nmajor = 1\nminor = 0\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "pyproject.toml")
            with open(config_path, "w") as f:
                f.write(content)
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = update_semantic_in_config("major", 2)
                assert result is True
                with open(config_path) as f:
                    updated = f.read()
                assert "major = 2" in updated
                assert "minor = 0" in updated
            finally:
                os.chdir(original_dir)

    def test_updates_minor_in_pyproject_toml(self):
        content = "[tool.bumpcalver]\nmajor = 1\nminor = 0\npatch = 0\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "pyproject.toml")
            with open(config_path, "w") as f:
                f.write(content)
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                update_semantic_in_config("minor", 5)
                with open(config_path) as f:
                    updated = f.read()
                assert "minor = 5" in updated
                assert "major = 1" in updated
            finally:
                os.chdir(original_dir)

    def test_returns_false_when_key_not_found(self):
        content = "[tool.bumpcalver]\nversion_format = \"{current_date}\"\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "pyproject.toml")
            with open(config_path, "w") as f:
                f.write(content)
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = update_semantic_in_config("major", 1)
                assert result is False
            finally:
                os.chdir(original_dir)

    def test_returns_false_when_no_config_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = update_semantic_in_config("major", 1)
                assert result is False
            finally:
                os.chdir(original_dir)

    def test_updates_bumpcalver_toml(self):
        content = "[tool.bumpcalver]\nmajor = 0\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "bumpcalver.toml")
            with open(config_path, "w") as f:
                f.write(content)
            original_dir = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = update_semantic_in_config("major", 3)
                assert result is True
                with open(config_path) as f:
                    updated = f.read()
                assert "major = 3" in updated
            finally:
                os.chdir(original_dir)


# ---------------------------------------------------------------------------
# CLI --bump-major / --bump-minor / --bump-patch
# ---------------------------------------------------------------------------

class TestCliBumpFlags:
    def _base_config(self, major=1, minor=0, patch=0):
        return {
            "version_format": "{major}.{minor}-{current_date}.{build_count}",
            "date_format": "%Y%m%d",
            "timezone": "UTC",
            "file_configs": [{"path": "/fake/file.toml", "file_type": "toml", "variable": "project.version"}],
            "git_tag": False,
            "auto_commit": False,
            "major": major,
            "minor": minor,
            "patch": patch,
        }

    def test_bump_major_resets_minor_and_patch(self):
        runner = CliRunner()
        with mock.patch("src.bumpcalver.cli.load_config", return_value=self._base_config(major=1, minor=2, patch=3)), \
             mock.patch("src.bumpcalver.cli.update_semantic_in_config") as mock_update, \
             mock.patch("src.bumpcalver.cli.get_build_version", return_value="2.0-20260518.1"), \
             mock.patch("src.bumpcalver.cli.update_version_in_files", return_value=["/fake/file.toml"]), \
             mock.patch("src.bumpcalver.cli.get_version_handler"), \
             mock.patch("src.bumpcalver.cli.BackupManager"), \
             mock.patch("src.bumpcalver.cli.backup_files_before_update", return_value=({}, None)), \
             mock.patch("src.bumpcalver.cli.generate_operation_id", return_value="test-op-id"):
            result = runner.invoke(main, ["--build", "--bump", "major"])
            assert result.exit_code == 0
            calls = {call[0] for call in mock_update.call_args_list}
            assert ("major", 2) in calls
            assert ("minor", 0) in calls
            assert ("patch", 0) in calls

    def test_bump_minor_resets_patch(self):
        runner = CliRunner()
        with mock.patch("src.bumpcalver.cli.load_config", return_value=self._base_config(major=1, minor=0, patch=5)), \
             mock.patch("src.bumpcalver.cli.update_semantic_in_config") as mock_update, \
             mock.patch("src.bumpcalver.cli.get_build_version", return_value="1.1-20260518.1"), \
             mock.patch("src.bumpcalver.cli.update_version_in_files", return_value=["/fake/file.toml"]), \
             mock.patch("src.bumpcalver.cli.get_version_handler"), \
             mock.patch("src.bumpcalver.cli.BackupManager"), \
             mock.patch("src.bumpcalver.cli.backup_files_before_update", return_value=({}, None)), \
             mock.patch("src.bumpcalver.cli.generate_operation_id", return_value="test-op-id"):
            result = runner.invoke(main, ["--build", "--bump", "minor"])
            assert result.exit_code == 0
            calls = {call[0] for call in mock_update.call_args_list}
            assert ("minor", 1) in calls
            assert ("patch", 0) in calls

    def test_bump_patch(self):
        runner = CliRunner()
        with mock.patch("src.bumpcalver.cli.load_config", return_value=self._base_config(major=1, minor=0, patch=2)), \
             mock.patch("src.bumpcalver.cli.update_semantic_in_config") as mock_update, \
             mock.patch("src.bumpcalver.cli.get_build_version", return_value="1.0-20260518.1"), \
             mock.patch("src.bumpcalver.cli.update_version_in_files", return_value=["/fake/file.toml"]), \
             mock.patch("src.bumpcalver.cli.get_version_handler"), \
             mock.patch("src.bumpcalver.cli.BackupManager"), \
             mock.patch("src.bumpcalver.cli.backup_files_before_update", return_value=({}, None)), \
             mock.patch("src.bumpcalver.cli.generate_operation_id", return_value="test-op-id"):
            result = runner.invoke(main, ["--build", "--bump", "patch"])
            assert result.exit_code == 0
            calls = {call[0] for call in mock_update.call_args_list}
            assert ("patch", 3) in calls

    def test_invalid_bump_value_error(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--bump", "invalid"])
        assert result.exit_code != 0

    def test_bump_with_undo_error(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--bump", "major", "--undo"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Regression: existing CalVer formats still work
# ---------------------------------------------------------------------------

class TestRegressionPureCalVer:
    def test_parse_version_yy_mm_dd_build(self):
        result = parse_version("26.05.18.001", "{current_date}.{build_count:03}", "%y.%m.%d")
        assert result == ("26.05.18", 1)

    def test_parse_version_yyyymmdd_compact(self):
        result = parse_version("20260518.001", "{current_date}.{build_count:03}", "%Y%m%d")
        assert result == ("20260518", 1)

    def test_parse_version_quarterly(self):
        result = parse_version("26.Q2.001", "{current_date}.{build_count:03}", "%y.Q%q")
        assert result == ("26.Q2", 1)

    def test_parse_version_legacy_format(self):
        result = parse_version("2024-12-07-001")
        assert result == ("2024-12-07", 1)

    def test_is_hybrid_format_false_for_pure_calver(self):
        assert _is_hybrid_format("{current_date}.{build_count:03}") is False
