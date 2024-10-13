# test_git_utils.py

import subprocess
from unittest import mock

import pytest
from src.bumpcalver.git_utils import create_git_tag


def test_create_git_tag_tag_exists(monkeypatch, capsys):
    """Test that the function exits gracefully when the tag already exists."""

    def mock_run(cmd, capture_output=False, text=False, check=False, stdout=None):
        if cmd == ["git", "tag", "-l", "v1.0.0"]:
            # Simulate that the tag exists
            mock_result = mock.Mock()
            mock_result.stdout = "v1.0.0\n"
            return mock_result
        return mock.DEFAULT

    monkeypatch.setattr(subprocess, "run", mock_run)

    create_git_tag("v1.0.0", [], False)

    captured = capsys.readouterr()
    assert "Tag 'v1.0.0' already exists. Skipping tag creation." in captured.out


def test_create_git_tag_no_tag_exists_no_autocommit(monkeypatch, capsys):
    """Test that the function creates a tag without committing files when auto_commit is False."""

    commands_executed = []

    def mock_run(cmd, **kwargs):
        commands_executed.append(cmd)
        if cmd == ["git", "tag", "-l", "v1.0.0"]:
            # Simulate that the tag does not exist
            mock_result = mock.Mock()
            mock_result.stdout = ""
            return mock_result
        elif cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
            # Simulate being inside a Git repository
            return mock.Mock()
        elif cmd == ["git", "tag", "v1.0.0"]:
            # Simulate successful tag creation
            return mock.Mock()
        else:
            raise ValueError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", mock_run)

    create_git_tag("v1.0.0", [], False)

    captured = capsys.readouterr()
    assert "Created Git tag 'v1.0.0'" in captured.out
    assert commands_executed == [
        ["git", "tag", "-l", "v1.0.0"],
        ["git", "rev-parse", "--is-inside-work-tree"],
        ["git", "tag", "v1.0.0"],
    ]


def test_create_git_tag_no_tag_exists_autocommit(monkeypatch, capsys):
    """Test that the function commits files and creates a tag when auto_commit is True."""

    commands_executed = []

    def mock_run(cmd, **kwargs):
        commands_executed.append(cmd)
        if cmd == ["git", "tag", "-l", "v1.0.0"]:
            # Simulate that the tag does not exist
            mock_result = mock.Mock()
            mock_result.stdout = ""
            return mock_result
        elif cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
            # Simulate being inside a Git repository
            return mock.Mock()
        elif cmd[0:2] == ["git", "add"]:
            # Simulate successful git add
            return mock.Mock()
        elif cmd == ["git", "commit", "-m", "Bump version to v1.0.0"]:
            # Simulate successful git commit
            return mock.Mock()
        elif cmd == ["git", "tag", "v1.0.0"]:
            # Simulate successful tag creation
            return mock.Mock()
        else:
            raise ValueError(f"Unexpected command: {cmd}")

    monkeypatch.setattr(subprocess, "run", mock_run)

    create_git_tag("v1.0.0", ["file1", "file2"], True)

    captured = capsys.readouterr()
    assert "Created Git tag 'v1.0.0'" in captured.out
    assert commands_executed == [
        ["git", "tag", "-l", "v1.0.0"],
        ["git", "rev-parse", "--is-inside-work-tree"],
        ["git", "add", "file1", "file2"],
        ["git", "commit", "-m", "Bump version to v1.0.0"],
        ["git", "tag", "v1.0.0"],
    ]


def test_create_git_tag_git_not_repository(monkeypatch, capsys):
    """Test that the function handles not being inside a Git repository."""

    def mock_run(cmd, **kwargs):
        if cmd == ["git", "tag", "-l", "v1.0.0"]:
            # Simulate that the tag does not exist
            mock_result = mock.Mock()
            mock_result.stdout = ""
            return mock_result
        elif cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
            # Simulate not being inside a Git repository
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd, output="error")
        else:
            return mock.Mock()

    monkeypatch.setattr(subprocess, "run", mock_run)

    create_git_tag("v1.0.0", [], False)

    captured = capsys.readouterr()
    assert "Error during Git operations:" in captured.out


def test_create_git_tag_git_commit_fails(monkeypatch, capsys):
    """Test that the function handles a failure during git commit."""

    def mock_run(cmd, **kwargs):
        if cmd == ["git", "tag", "-l", "v1.0.0"]:
            # Simulate that the tag does not exist
            mock_result = mock.Mock()
            mock_result.stdout = ""
            return mock_result
        elif cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
            return mock.Mock()
        elif cmd[0:2] == ["git", "add"]:
            return mock.Mock()
        elif cmd == ["git", "commit", "-m", "Bump version to v1.0.0"]:
            # Simulate git commit failure
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd, output="error")
        else:
            return mock.Mock()

    monkeypatch.setattr(subprocess, "run", mock_run)

    create_git_tag("v1.0.0", ["file1", "file2"], True)

    captured = capsys.readouterr()
    assert "Error during Git operations:" in captured.out


def test_create_git_tag_git_tag_fails(monkeypatch, capsys):
    """Test that the function handles a failure during git tag creation."""

    def mock_run(cmd, **kwargs):
        if cmd == ["git", "tag", "-l", "v1.0.0"]:
            # Simulate that the tag does not exist
            mock_result = mock.Mock()
            mock_result.stdout = ""
            return mock_result
        elif cmd == ["git", "rev-parse", "--is-inside-work-tree"]:
            return mock.Mock()
        elif cmd[0:2] == ["git", "add"]:
            return mock.Mock()
        elif cmd == ["git", "commit", "-m", "Bump version to v1.0.0"]:
            return mock.Mock()
        elif cmd == ["git", "tag", "v1.0.0"]:
            # Simulate git tag failure
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd, output="error")
        else:
            return mock.Mock()

    monkeypatch.setattr(subprocess, "run", mock_run)

    create_git_tag("v1.0.0", ["file1", "file2"], True)

    captured = capsys.readouterr()
    assert "Error during Git operations:" in captured.out


def test_create_git_tag_unexpected_exception(monkeypatch):
    """Test that unexpected exceptions are not caught by the function."""

    def mock_run(cmd, **kwargs):
        # Simulate an unexpected exception
        raise Exception("Unexpected error")

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(Exception, match="Unexpected error"):
        create_git_tag("v1.0.0", [], False)
