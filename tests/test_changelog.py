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