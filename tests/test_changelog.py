import json
import subprocess

import pytest
import src.bumpcalver.changelog as changelog
from src.bumpcalver.changelog import build_changelog_update, splice_changelog_entry


def test_splice_changelog_entry_inserts_after_heading():
    existing = "# Changelog\n\n## Latest Changes\n\n### older\n\nOld body\n"

    updated = splice_changelog_entry(
        existing_content=existing,
        version="2026.09.19",
        heading="## Latest Changes",
        entry_markdown="### 2026.09.19\n\n#### What's Changed\n* New change\n",
    )

    assert updated.index("### 2026.09.19") < updated.index("### older")
    assert "* New change" in updated


def test_splice_changelog_entry_replaces_same_version():
    existing = (
        "# Changelog\n\n## Latest Changes\n\n### 2026.09.19\n\n"
        "#### What's Changed\n* Old change\n\n### older\n\nOld body\n"
    )

    updated = splice_changelog_entry(
        existing_content=existing,
        version="2026.09.19",
        heading="## Latest Changes",
        entry_markdown="### 2026.09.19\n\n#### What's Changed\n* New change\n",
    )

    assert updated.count("### 2026.09.19") == 1
    assert "* New change" in updated
    assert "* Old change" not in updated


def test_build_changelog_update_creates_missing_file_content(monkeypatch, tmp_path):
    monkeypatch.setattr("src.bumpcalver.changelog._latest_reachable_tag", lambda: "v2026.09.18.001")
    monkeypatch.setattr(
        "src.bumpcalver.changelog._commit_subjects_since",
        lambda previous_tag: ["Add changelog option", "Improve docs"],
    )

    update = build_changelog_update(
        changelog_path=str(tmp_path / "CHANGELOG.md"),
        version="2026.09.19",
        heading="## Latest Changes",
        timezone="UTC",
    )

    assert update.changed is True
    assert "# Changelog" in update.updated_content
    assert "### 2026.09.19" in update.updated_content
    assert "Add changelog option" in update.updated_content


def test_build_changelog_update_uses_openai_rewrite(monkeypatch, tmp_path):
    monkeypatch.setattr("src.bumpcalver.changelog._latest_reachable_tag", lambda: "v2026.09.18.001")
    monkeypatch.setattr(
        "src.bumpcalver.changelog._commit_subjects_since",
        lambda previous_tag: ["Add changelog option"],
    )
    monkeypatch.setattr(
        "src.bumpcalver.changelog._rewrite_entry_with_openai",
        lambda **kwargs: "### 2026.09.19\n\n#### What's Changed\n* Rewritten by AI\n",
    )

    update = build_changelog_update(
        changelog_path=str(tmp_path / "CHANGELOG.md"),
        version="2026.09.19",
        heading="## Latest Changes",
        timezone="UTC",
        ai_provider="openai",
        ai_model="gpt-4.1-2025-04-14",
    )

    assert "Rewritten by AI" in update.updated_content


def test_build_changelog_update_rejects_unknown_provider(monkeypatch, tmp_path):
    monkeypatch.setattr("src.bumpcalver.changelog._latest_reachable_tag", lambda: None)
    monkeypatch.setattr("src.bumpcalver.changelog._commit_subjects_since", lambda previous_tag: [])

    with pytest.raises(ValueError, match="Unsupported changelog AI provider"):
        build_changelog_update(
            changelog_path=str(tmp_path / "CHANGELOG.md"),
            version="2026.09.19",
            heading="## Latest Changes",
            timezone="UTC",
            ai_provider="bogus",
        )


def test_write_changelog_update_creates_parent_directory(tmp_path):
    update = changelog.ChangelogUpdate(
        path=str(tmp_path / "nested" / "CHANGELOG.md"),
        version="2026.09.19",
        heading="## Latest Changes",
        previous_tag=None,
        commit_subjects=[],
        entry_markdown="### 2026.09.19\n",
        updated_content="# Changelog\n",
        changed=True,
    )

    changelog.write_changelog_update(update)

    assert (tmp_path / "nested" / "CHANGELOG.md").read_text(encoding="utf-8") == "# Changelog\n"


def test_ensure_heading_adds_missing_heading_and_preserves_existing_newline():
    assert changelog._ensure_heading("# Changelog", "## Latest Changes") == (
        "# Changelog\n\n## Latest Changes\n\n"
    )
    assert changelog._ensure_heading("# Changelog\n## Latest Changes\n", "## Latest Changes") == (
        "# Changelog\n## Latest Changes\n"
    )
    assert changelog._ensure_heading("# Changelog\n## Latest Changes", "## Latest Changes") == (
        "# Changelog\n## Latest Changes\n"
    )


def test_format_timestamp_falls_back_to_utc_for_invalid_timezone():
    timestamp = changelog._format_timestamp("Not/AZone")

    assert isinstance(timestamp, str)
    assert ", " in timestamp


def test_latest_reachable_tag_returns_none_on_git_errors(monkeypatch):
    def _raise(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "git")

    monkeypatch.setattr("src.bumpcalver.changelog.subprocess.run", _raise)

    assert changelog._latest_reachable_tag() is None


def test_latest_reachable_tag_returns_stripped_tag(monkeypatch):
    class Result:
        stdout = "v2026.09.18.001\n"

    monkeypatch.setattr("src.bumpcalver.changelog.subprocess.run", lambda *args, **kwargs: Result())

    assert changelog._latest_reachable_tag() == "v2026.09.18.001"


def test_commit_subjects_since_handles_git_errors(monkeypatch):
    def _raise(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr("src.bumpcalver.changelog.subprocess.run", _raise)

    assert changelog._commit_subjects_since("v2026.09.18.001") == []


def test_commit_subjects_since_deduplicates_and_skips_blank_lines(monkeypatch):
    class Result:
        stdout = "Add feature\n\nAdd feature\nFix bug\n"

    monkeypatch.setattr("src.bumpcalver.changelog.subprocess.run", lambda *args, **kwargs: Result())

    assert changelog._commit_subjects_since("v2026.09.18.001") == ["Add feature", "Fix bug"]


def test_rewrite_entry_with_openai_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY must be set"):
        changelog._rewrite_entry_with_openai(
            entry_markdown="### 2026.09.19\n",
            version="2026.09.19",
            commit_subjects=["Add feature"],
            previous_tag=None,
            model="gpt-4.1-2025-04-14",
        )


def test_rewrite_entry_with_openai_handles_url_errors(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def _raise(_request):
        raise changelog.urllib_error.URLError("boom")

    monkeypatch.setattr("src.bumpcalver.changelog.urllib_request.urlopen", _raise)

    with pytest.raises(ValueError, match="OpenAI changelog rewrite failed"):
        changelog._rewrite_entry_with_openai(
            entry_markdown="### 2026.09.19\n",
            version="2026.09.19",
            commit_subjects=["Add feature"],
            previous_tag=None,
            model="gpt-4.1-2025-04-14",
        )


def test_rewrite_entry_with_openai_rejects_non_object_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(["not-an-object"]).encode("utf-8")

    monkeypatch.setattr(
        "src.bumpcalver.changelog.urllib_request.urlopen", lambda _request: Response()
    )

    with pytest.raises(ValueError, match="non-object response"):
        changelog._rewrite_entry_with_openai(
            entry_markdown="### 2026.09.19\n",
            version="2026.09.19",
            commit_subjects=["Add feature"],
            previous_tag=None,
            model="gpt-4.1-2025-04-14",
        )


def test_rewrite_entry_with_openai_rejects_empty_content(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            payload = {"choices": [{"message": {"content": ""}}]}
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(
        "src.bumpcalver.changelog.urllib_request.urlopen", lambda _request: Response()
    )

    with pytest.raises(ValueError, match="returned no content"):
        changelog._rewrite_entry_with_openai(
            entry_markdown="### 2026.09.19\n",
            version="2026.09.19",
            commit_subjects=["Add feature"],
            previous_tag=None,
            model="gpt-4.1-2025-04-14",
        )


def test_rewrite_entry_with_openai_rejects_invalid_markdown(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            payload = {"choices": [{"message": {"content": "Not markdown"}}]}
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(
        "src.bumpcalver.changelog.urllib_request.urlopen", lambda _request: Response()
    )

    with pytest.raises(ValueError, match="did not return a valid changelog entry"):
        changelog._rewrite_entry_with_openai(
            entry_markdown="### 2026.09.19\n",
            version="2026.09.19",
            commit_subjects=["Add feature"],
            previous_tag=None,
            model="gpt-4.1-2025-04-14",
        )


def test_rewrite_entry_with_openai_returns_rewritten_markdown(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            payload = {
                "choices": [
                    {"message": {"content": "### 2026.09.19\n\n#### What's Changed\n* Rewritten\n"}}
                ]
            }
            return json.dumps(payload).encode("utf-8")

    def _urlopen(request):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return Response()

    monkeypatch.setattr("src.bumpcalver.changelog.urllib_request.urlopen", _urlopen)

    result = changelog._rewrite_entry_with_openai(
        entry_markdown="### 2026.09.19\n",
        version="2026.09.19",
        commit_subjects=["Add feature"],
        previous_tag="v2026.09.18.001",
        model="gpt-4.1-2025-04-14",
    )

    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["body"]["model"] == "gpt-4.1-2025-04-14"
    assert result.endswith("\n")
    assert "Rewritten" in result
