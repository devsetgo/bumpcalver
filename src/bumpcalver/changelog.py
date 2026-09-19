"""Changelog generation helpers for bumpcalver.

This module generates a deterministic changelog draft from local git history,
optionally rewrites that draft with OpenAI, and splices the result into a
 changelog file under a configured heading.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request
from zoneinfo import ZoneInfo

OPENAI_API_ENV_VAR = "OPENAI_API_KEY"
DEFAULT_OPENAI_MODEL = "gpt-4.1-2025-04-14"


@dataclass(frozen=True)
class ChangelogUpdate:
    """Prepared changelog write for a single version bump."""

    path: str
    version: str
    heading: str
    previous_tag: Optional[str]
    commit_subjects: List[str]
    entry_markdown: str
    updated_content: str
    changed: bool


def build_changelog_update(
    *,
    changelog_path: str,
    version: str,
    heading: str = "## Latest Changes",
    timezone: str = "UTC",
    ai_provider: str = "none",
    ai_model: Optional[str] = None,
) -> ChangelogUpdate:
    """Prepare a changelog update for the given version.

    The returned object contains the generated entry and the full file contents
    after insertion/replacement, but does not write anything itself.
    """
    path = Path(changelog_path)
    existing_content = (
        path.read_text(encoding="utf-8") if path.exists() else _default_changelog_content(heading)
    )

    previous_tag = _latest_reachable_tag()
    commit_subjects = _commit_subjects_since(previous_tag)
    entry_markdown = render_changelog_entry(
        version=version,
        commit_subjects=commit_subjects,
        previous_tag=previous_tag,
        timezone=timezone,
    )

    if ai_provider == "openai":
        entry_markdown = _rewrite_entry_with_openai(
            entry_markdown=entry_markdown,
            version=version,
            commit_subjects=commit_subjects,
            previous_tag=previous_tag,
            model=ai_model or DEFAULT_OPENAI_MODEL,
        )
    elif ai_provider != "none":
        raise ValueError(f"Unsupported changelog AI provider: {ai_provider}")

    updated_content = splice_changelog_entry(
        existing_content=existing_content,
        version=version,
        heading=heading,
        entry_markdown=entry_markdown,
    )

    return ChangelogUpdate(
        path=str(path),
        version=version,
        heading=heading,
        previous_tag=previous_tag,
        commit_subjects=commit_subjects,
        entry_markdown=entry_markdown,
        updated_content=updated_content,
        changed=updated_content != existing_content,
    )


def render_changelog_entry(
    *,
    version: str,
    commit_subjects: List[str],
    previous_tag: Optional[str],
    timezone: str,
) -> str:
    """Render a deterministic markdown entry for a version."""
    normalized_commits = commit_subjects or ["Version maintenance updates"]
    lines = [f"### {version}", ""]
    if previous_tag:
        lines.extend([f"_Changes since {previous_tag}._", ""])
    lines.append("#### What's Changed")
    for subject in normalized_commits:
        lines.append(f"* {subject}")
    lines.extend(["", f"Generated Date: {_format_timestamp(timezone)}", ""])
    return "\n".join(lines)


def splice_changelog_entry(
    *,
    existing_content: str,
    version: str,
    heading: str,
    entry_markdown: str,
) -> str:
    """Insert or replace the latest entry under the configured heading."""
    content = _ensure_heading(existing_content, heading)
    entry = entry_markdown.rstrip() + "\n\n"

    lines = content.splitlines(keepends=True)
    heading_index = _find_line_index(lines, heading)
    if heading_index is None:
        raise ValueError(f"Could not find changelog heading: {heading}")

    insertion_index = heading_index + 1
    while insertion_index < len(lines) and lines[insertion_index].strip() == "":
        insertion_index += 1

    entry_heading = f"### {version}"
    existing_start = _find_line_index(lines, entry_heading, start=insertion_index)

    if existing_start is not None:
        existing_end = existing_start + 1
        while existing_end < len(lines):
            current_line = lines[existing_end]
            if current_line.startswith("### "):
                break
            existing_end += 1
        lines[existing_start:existing_end] = [entry]
    else:
        lines[insertion_index:insertion_index] = [entry]

    return "".join(lines)


def write_changelog_update(update: ChangelogUpdate) -> None:
    """Write a prepared changelog update to disk."""
    path = Path(update.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(update.updated_content, encoding="utf-8")


def _default_changelog_content(heading: str) -> str:
    return "# Changelog\nAll notable changes to this project will be documented in this file.\n\n" + heading + "\n\n"


def _ensure_heading(existing_content: str, heading: str) -> str:
    lines = existing_content.splitlines()
    if any(line.strip() == heading for line in lines):
        if existing_content.endswith("\n"):
            return existing_content
        return existing_content + "\n"

    suffix = existing_content
    if suffix and not suffix.endswith("\n"):
        suffix += "\n"
    if suffix and not suffix.endswith("\n\n"):
        suffix += "\n"
    return suffix + heading + "\n\n"


def _find_line_index(lines: List[str], target: str, start: int = 0) -> Optional[int]:
    for index in range(start, len(lines)):
        if lines[index].strip() == target:
            return index
    return None


def _format_timestamp(timezone: str) -> str:
    try:
        tzinfo = ZoneInfo(timezone)
    except Exception:
        tzinfo = ZoneInfo("UTC")
    return datetime.now(tzinfo).strftime("%Y %B %d, %H:%M")


def _latest_reachable_tag() -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    tag = result.stdout.strip()
    return tag or None


def _commit_subjects_since(previous_tag: Optional[str]) -> List[str]:
    command = ["git", "log", "--format=%s"]
    if previous_tag:
        command.append(f"{previous_tag}..HEAD")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    seen = set()
    subjects: List[str] = []
    for line in result.stdout.splitlines():
        subject = line.strip()
        if not subject or subject in seen:
            continue
        seen.add(subject)
        subjects.append(subject)
    return subjects


def _rewrite_entry_with_openai(
    *,
    entry_markdown: str,
    version: str,
    commit_subjects: List[str],
    previous_tag: Optional[str],
    model: str,
) -> str:
    api_key = os.getenv(OPENAI_API_ENV_VAR)
    if not api_key:
        raise ValueError(
            f"{OPENAI_API_ENV_VAR} must be set when changelog AI provider is 'openai'."
        )

    system_prompt = (
        "You rewrite markdown changelog entries. Respond with ONLY markdown for a single changelog "
        "entry, with no code fences. Preserve the top heading line, keep exactly one '#### What\'s "
        "Changed' section, summarize repetitive commit bullets when appropriate, and do not invent "
        "changes that are not present in the provided commit subjects or draft entry."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "version": version,
                        "previous_tag": previous_tag,
                        "commit_subjects": commit_subjects,
                        "draft_entry": entry_markdown,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
        "max_tokens": 800,
        "temperature": 0.3,
    }
    request = urllib_request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(request) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib_error.URLError as exc:
        raise ValueError(f"OpenAI changelog rewrite failed: {exc}") from exc

    if not isinstance(response_payload, dict):
        raise ValueError("OpenAI changelog rewrite returned a non-object response.")

    choices: Any = response_payload.get("choices", [])
    first_choice: Dict[str, Any] = choices[0] if isinstance(choices, list) and choices else {}
    message: Dict[str, Any] = (
        first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
    )
    raw_content = message.get("content", "") if isinstance(message, dict) else ""
    content = raw_content.strip() if isinstance(raw_content, str) else ""
    if not content:
        raise ValueError("OpenAI changelog rewrite returned no content.")

    if not re.search(r"^###\s+", content, re.MULTILINE):
        raise ValueError("OpenAI changelog rewrite did not return a valid changelog entry.")

    return content.rstrip() + "\n"