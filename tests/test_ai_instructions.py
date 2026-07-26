# tests/test_ai_instructions.py
"""Tests for the packaged AI-assistant integration instructions feature.

See IMPROVEMENTS.md §6 / ADD_AI_INSTRUCTIONS.md for the full rationale —
this ships app-integration guidance as package data (src/bumpcalver/assets/ai/)
with a small API + CLI to read/bootstrap it, so it can't drift out of sync
with an externally copy-pasted snippet.
"""

import pytest
from src.bumpcalver import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)
from src.bumpcalver.ai_instructions import _resolve_output_path, main


def test_available_instruction_profiles_contains_expected_profiles():
    assert available_instruction_profiles() == ("claude", "copilot", "generic")


def test_get_app_instructions_contains_core_config_token():
    # Regression guard against the instructions rotting out of sync with the
    # actual config schema: `[[tool.bumpcalver.file]]` is the load-bearing
    # token every real bumpcalver config needs at least one of.
    for profile in available_instruction_profiles():
        text = get_app_instructions(profile)
        assert "[[tool.bumpcalver.file]]" in text
        assert "file_type" in text


def test_get_app_instructions_documents_every_builtin_file_type():
    # Also a drift guard: if handlers.py's _HANDLER_REGISTRY gains/loses an
    # entry without the instructions being updated, this should catch it.
    from src.bumpcalver.handlers import _HANDLER_REGISTRY

    text = get_app_instructions("generic")
    for file_type in _HANDLER_REGISTRY:
        assert f"`{file_type}`" in text, f"file_type {file_type!r} not documented"


def test_get_app_instructions_supports_aliases():
    assert get_app_instructions("github-copilot") == get_app_instructions("copilot")
    assert get_app_instructions("anthropic-claude") == get_app_instructions("claude")
    assert get_app_instructions("default") == get_app_instructions("generic")


def test_get_app_instructions_unknown_profile_raises():
    with pytest.raises(ValueError, match="Unsupported instruction profile"):
        get_app_instructions("unknown-assistant")


def test_suggested_instruction_filename_is_profile_specific():
    assert suggested_instruction_filename("copilot") == ".github/copilot-instructions.md"
    assert suggested_instruction_filename("claude") == "CLAUDE.md"
    assert suggested_instruction_filename("generic") == "AI_INSTRUCTIONS.md"


def test_cli_prints_to_stdout_by_default(capsys):
    exit_code = main(["claude"])
    assert exit_code == 0
    assert capsys.readouterr().out == get_app_instructions("claude")


def test_cli_write_flag_uses_suggested_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["copilot", "--write"]) == 0
    written = tmp_path / ".github" / "copilot-instructions.md"
    assert written.read_text(encoding="utf-8") == get_app_instructions("copilot")


def test_cli_output_flag_writes_explicit_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "nested" / "INSTRUCTIONS.md"
    assert main(["generic", "--output", str(destination)]) == 0
    assert destination.read_text(encoding="utf-8") == get_app_instructions("generic")


def test_cli_unknown_profile_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["unknown-assistant"])
    assert exc_info.value.code == 2
    assert "Unsupported instruction profile" in capsys.readouterr().err


# --- Security regression tests: do not weaken or remove these. ---


def test_cli_output_flag_rejects_path_traversal_outside_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    escape_target = tmp_path.parent / "escaped.md"
    escape_target.unlink(missing_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["generic", "--output", "../escaped.md"])
    assert exc_info.value.code == 2
    assert not escape_target.exists()


def test_cli_output_flag_rejects_absolute_path_outside_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / "other-dir"
    outside.mkdir(exist_ok=True)
    escape_target = outside / "escaped.md"
    escape_target.unlink(missing_ok=True)
    with pytest.raises(SystemExit) as exc_info:
        main(["generic", "--output", str(escape_target)])
    assert exc_info.value.code == 2
    assert not escape_target.exists()


def test_cli_output_flag_allows_dotdot_that_stays_inside_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "subdir").mkdir()
    assert main(["generic", "--output", "subdir/../ALLOWED.md"]) == 0
    assert (tmp_path / "ALLOWED.md").read_text(encoding="utf-8") == get_app_instructions("generic")


def test_resolve_output_path_rejects_sibling_directory_with_shared_prefix(tmp_path):
    base = tmp_path / "project"
    base.mkdir()
    sibling = tmp_path / "project-evil" / "file.md"
    with pytest.raises(ValueError, match="Refusing to write outside"):
        _resolve_output_path(str(sibling), base_dir=base)
