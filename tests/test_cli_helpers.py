# tests/test_cli_helpers.py
"""Direct unit tests for the helper functions extracted from cli.main().

These exercise each piece of the version-bump pipeline in isolation, rather
than only indirectly through full CliRunner invocations of main() (see
test_cli.py for those). Keeping both: the CliRunner tests catch wiring/option
mistakes, these catch logic mistakes in each piece without needing to drive
the whole CLI.
"""

import subprocess
from unittest import mock

from src.bumpcalver.cli import (
    _all_files_already_updated,
    _apply_semantic_bump,
    _compute_new_version,
    _create_git_tag_and_commit,
    _read_current_version,
)


# --- _read_current_version -------------------------------------------------


def test_read_current_version_success():
    file_config = {"path": "version.py", "file_type": "python", "variable": "__version__"}
    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "1.2.3"

    with mock.patch(
        "src.bumpcalver.cli.get_version_handler", return_value=mock_handler
    ) as mock_get_handler:
        result = _read_current_version(file_config)

    assert result == "1.2.3"
    mock_get_handler.assert_called_once_with("python")
    mock_handler.read_version.assert_called_once_with("version.py", "__version__")


def test_read_current_version_passes_directive():
    file_config = {
        "path": "dockerfile",
        "file_type": "dockerfile",
        "variable": "VERSION",
        "directive": "ARG",
    }
    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "1.0.0"

    with mock.patch("src.bumpcalver.cli.get_version_handler", return_value=mock_handler):
        result = _read_current_version(file_config)

    assert result == "1.0.0"
    mock_handler.read_version.assert_called_once_with(
        "dockerfile", "VERSION", directive="ARG"
    )


def test_read_current_version_passes_pattern():
    file_config = {
        "path": "version.rb",
        "file_type": "regex",
        "variable": "VERSION",
        "pattern": r'VERSION = "(.+?)"',
    }
    mock_handler = mock.Mock()
    mock_handler.read_version.return_value = "1.0.0"

    with mock.patch("src.bumpcalver.cli.get_version_handler", return_value=mock_handler):
        result = _read_current_version(file_config)

    assert result == "1.0.0"
    mock_handler.read_version.assert_called_once_with(
        "version.rb", "VERSION", pattern=r'VERSION = "(.+?)"'
    )


def test_read_current_version_unsupported_file_type_returns_none():
    file_config = {"path": "x", "file_type": "nonexistent", "variable": "v"}
    with mock.patch(
        "src.bumpcalver.cli.get_version_handler", side_effect=ValueError("nope")
    ):
        assert _read_current_version(file_config) is None


def test_read_current_version_handler_exception_returns_none():
    file_config = {"path": "x", "file_type": "python", "variable": "v"}
    mock_handler = mock.Mock()
    mock_handler.read_version.side_effect = RuntimeError("boom")

    with mock.patch("src.bumpcalver.cli.get_version_handler", return_value=mock_handler):
        assert _read_current_version(file_config) is None


# --- _apply_semantic_bump ----------------------------------------------------


def test_apply_semantic_bump_none_leaves_values_unchanged():
    with mock.patch("src.bumpcalver.cli.update_semantic_in_config") as mock_update:
        result = _apply_semantic_bump(None, 1, 2, 3)

    assert result == (1, 2, 3)
    mock_update.assert_not_called()


def test_apply_semantic_bump_major_resets_minor_and_patch():
    with mock.patch("src.bumpcalver.cli.update_semantic_in_config") as mock_update:
        result = _apply_semantic_bump("major", 1, 2, 3)

    assert result == (2, 0, 0)
    mock_update.assert_has_calls(
        [mock.call("major", 2), mock.call("minor", 0), mock.call("patch", 0)]
    )


def test_apply_semantic_bump_minor_resets_patch_only():
    with mock.patch("src.bumpcalver.cli.update_semantic_in_config") as mock_update:
        result = _apply_semantic_bump("minor", 1, 2, 3)

    assert result == (1, 3, 0)
    mock_update.assert_has_calls([mock.call("minor", 3), mock.call("patch", 0)])


def test_apply_semantic_bump_patch_increments_patch_only():
    with mock.patch("src.bumpcalver.cli.update_semantic_in_config") as mock_update:
        result = _apply_semantic_bump("patch", 1, 2, 3)

    assert result == (1, 2, 4)
    mock_update.assert_called_once_with("patch", 4)


# --- _compute_new_version ----------------------------------------------------


def test_compute_new_version_plain_date(monkeypatch):
    monkeypatch.setattr(
        "src.bumpcalver.cli.get_current_datetime_version", lambda tz, fmt: "2026.01.01"
    )
    result = _compute_new_version(
        build=False,
        beta=False,
        rc=False,
        release=False,
        custom=None,
        file_configs=[{"path": "v.py"}],
        version_format="{current_date}",
        timezone="UTC",
        date_format="%Y.%m.%d",
        config={},
        config_major=0,
        config_minor=0,
        config_patch=0,
        cached_version=lambda fc: None,
    )
    assert result == "2026.01.01"


def test_compute_new_version_build_uses_get_build_version(monkeypatch):
    captured = {}

    def fake_get_build_version(file_config, version_format, timezone, date_format, **kwargs):
        captured["kwargs"] = kwargs
        return "2026.01.01-001"

    monkeypatch.setattr("src.bumpcalver.cli.get_build_version", fake_get_build_version)

    result = _compute_new_version(
        build=True,
        beta=False,
        rc=False,
        release=False,
        custom=None,
        file_configs=[{"path": "v.py"}],
        version_format="{current_date}-{build_count:03}",
        timezone="UTC",
        date_format="%Y.%m.%d",
        config={},
        config_major=1,
        config_minor=2,
        config_patch=3,
        cached_version=lambda fc: None,
    )

    assert result == "2026.01.01-001"
    assert captured["kwargs"] == {"major": 1, "minor": 2, "patch": 3}


def test_compute_new_version_applies_beta_suffix(monkeypatch):
    monkeypatch.setattr(
        "src.bumpcalver.cli.get_current_datetime_version", lambda tz, fmt: "2026.01.01"
    )
    result = _compute_new_version(
        build=False,
        beta=True,
        rc=False,
        release=False,
        custom=None,
        file_configs=[{"path": "v.py"}],
        version_format="{current_date}",
        timezone="UTC",
        date_format="%Y.%m.%d",
        config={},
        config_major=0,
        config_minor=0,
        config_patch=0,
        cached_version=lambda fc: "2025.12.31",
    )
    assert result == "2026.01.01.beta"


def test_compute_new_version_applies_custom_suffix(monkeypatch):
    monkeypatch.setattr(
        "src.bumpcalver.cli.get_current_datetime_version", lambda tz, fmt: "2026.01.01"
    )
    result = _compute_new_version(
        build=False,
        beta=False,
        rc=False,
        release=False,
        custom="hotfix",
        file_configs=[{"path": "v.py"}],
        version_format="{current_date}",
        timezone="UTC",
        date_format="%Y.%m.%d",
        config={},
        config_major=0,
        config_minor=0,
        config_patch=0,
        cached_version=lambda fc: None,
    )
    assert result == "2026.01.01.hotfix"


# --- _all_files_already_updated -----------------------------------------------


def test_all_files_already_updated_true_when_every_file_matches():
    file_configs = [{"path": "a"}, {"path": "b"}]
    assert _all_files_already_updated(file_configs, "1.0", lambda fc: "1.0") is True


def test_all_files_already_updated_false_on_any_mismatch():
    file_configs = [{"path": "a"}, {"path": "b"}]
    versions = {"a": "1.0", "b": "0.9"}
    assert (
        _all_files_already_updated(
            file_configs, "1.0", lambda fc: versions[fc["path"]]
        )
        is False
    )


def test_all_files_already_updated_false_when_read_fails():
    file_configs = [{"path": "a"}]
    assert _all_files_already_updated(file_configs, "1.0", lambda fc: None) is False


# --- _create_git_tag_and_commit ------------------------------------------------


def test_create_git_tag_and_commit_disabled_does_nothing():
    with mock.patch("src.bumpcalver.cli.create_git_tag") as mock_create_tag:
        result = _create_git_tag_and_commit("1.0", ["a.py"], git_tag=False, auto_commit=False)

    assert result == (None, None)
    mock_create_tag.assert_not_called()


def test_create_git_tag_and_commit_tag_only():
    with mock.patch("src.bumpcalver.cli.create_git_tag") as mock_create_tag:
        result = _create_git_tag_and_commit("1.0", ["a.py"], git_tag=True, auto_commit=False)

    assert result == (None, "1.0")
    mock_create_tag.assert_called_once_with("1.0", ["a.py"], False)


def test_create_git_tag_and_commit_with_auto_commit_reads_hash():
    with mock.patch("src.bumpcalver.cli.create_git_tag") as mock_create_tag, mock.patch(
        "src.bumpcalver.cli.subprocess.run"
    ) as mock_run:
        mock_run.return_value = mock.Mock(stdout="abc123\n")
        result = _create_git_tag_and_commit("1.0", ["a.py"], git_tag=True, auto_commit=True)

    assert result == ("abc123", "1.0")
    mock_create_tag.assert_called_once_with("1.0", ["a.py"], True)
    mock_run.assert_called_once_with(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )


def test_create_git_tag_and_commit_swallows_git_failure():
    with mock.patch(
        "src.bumpcalver.cli.create_git_tag",
        side_effect=subprocess.CalledProcessError(1, "git"),
    ):
        result = _create_git_tag_and_commit("1.0", ["a.py"], git_tag=True, auto_commit=False)

    assert result == (None, None)
