"""AI-assistant integration instructions, packaged with the library.

Ships the current, verified integration guidance as package data so it can
never drift out of sync with an external copy-pasted snippet. See the
package's top-level docstring / `cli.main`'s docstring for the
discoverability hook that points an AI assistant at this without being asked.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

_PROFILE_ALIASES: dict[str, str] = {
    "generic": "generic",
    "default": "generic",
    "copilot": "copilot",
    "github-copilot": "copilot",
    "claude": "claude",
    "anthropic-claude": "claude",
    # Add more aliases here as needed, e.g. 'cursor': 'cursor'
}

_PROFILE_TO_ASSET: dict[str, str] = {
    "generic": "assets/ai/generic_app_instructions.md",
    "copilot": "assets/ai/copilot_app_instructions.md",
    "claude": "assets/ai/claude_app_instructions.md",
}


def available_instruction_profiles() -> tuple[str, ...]:
    """Return canonical app-integration instruction profiles bundled with the package."""
    return tuple(sorted(_PROFILE_TO_ASSET.keys()))


def suggested_instruction_filename(profile: str = "generic") -> str:
    """Return a suggested filename for app repositories.

    This is only a recommendation and is not written automatically unless
    the caller opts into --write / --output via the CLI.
    """
    normalized = _normalize_profile(profile)
    if normalized == "copilot":
        return ".github/copilot-instructions.md"
    if normalized == "claude":
        return "CLAUDE.md"
    return "AI_INSTRUCTIONS.md"


def get_app_instructions(profile: str = "generic") -> str:
    """Return packaged app-side integration instructions for an AI assistant profile.

    Aliases are accepted (for example: github-copilot, anthropic-claude).
    """
    normalized = _normalize_profile(profile)
    relative_path = _PROFILE_TO_ASSET[normalized]
    # __package__ rather than a hardcoded "bumpcalver" literal: this module
    # is imported both as the real installed package (bumpcalver.ai_instructions)
    # and, in this repo's own dev/test environment, via the src-layout path
    # (src.bumpcalver.ai_instructions) without an editable install — __package__
    # resolves correctly either way, since it's always the actual dotted
    # package path this module was imported under.
    package_root = resources.files(__package__)
    return (package_root / relative_path).read_text(encoding="utf-8")


def _normalize_profile(profile: str) -> str:
    key = (profile or "").strip().lower()
    normalized = _PROFILE_ALIASES.get(key)
    if normalized:
        return normalized
    supported = ", ".join(available_instruction_profiles())
    raise ValueError(
        f"Unsupported instruction profile: {profile!r}. Supported profiles: {supported}"
    )


def _resolve_output_path(destination: str, *, base_dir: Path) -> Path:
    """Resolve a CLI-supplied destination and confirm it stays within base_dir.

    SECURITY (do not skip this): `--output` is free-form text that may come
    from an LLM-orchestrated invocation of this CLI, not a trusted human
    typing a path by hand. Without this check, a value like
    `--output ../../../etc/cron.d/evil` or an absolute path would let the
    process write outside the project directory it was invoked in.
    Resolving (which also follows symlinks) and requiring the result to be
    a descendant of base_dir closes that off.
    """
    base = base_dir.resolve()
    candidate = Path(destination)
    if not candidate.is_absolute():
        candidate = base / candidate
    candidate = candidate.resolve()

    # NOTE: use `candidate.parents` containment, not a string-prefix check
    # like str(candidate).startswith(str(base)) — that wrongly treats a
    # sibling directory like "project-evil/" as being inside "project/".
    if candidate != base and base not in candidate.parents:
        raise ValueError(
            f"Refusing to write outside the current directory ({base}): "
            f"{destination!r} resolves to {candidate}"
        )
    return candidate


def main(argv: list[str] | None = None) -> int:
    """CLI: print or write packaged AI-assistant instructions for an app repo.

    Examples::

        python -m bumpcalver.ai_instructions claude > CLAUDE.md
        python -m bumpcalver.ai_instructions copilot --write
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m bumpcalver.ai_instructions",
        description="Print or write packaged AI-assistant instructions for app integrations.",
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default="generic",
        help=f"Instruction profile (aliases accepted). One of: {', '.join(available_instruction_profiles())}.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write to the suggested destination file (e.g. CLAUDE.md) instead of stdout.",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write to an explicit path instead of stdout or the suggested destination.",
    )
    args = parser.parse_args(argv)

    try:
        text = get_app_instructions(args.profile)
    except ValueError as exc:
        parser.error(str(exc))
        return 2  # pragma: no cover — parser.error() always exits the process

    destination = args.output or (
        suggested_instruction_filename(args.profile) if args.write else None
    )
    if destination is None:
        sys.stdout.write(text)
        return 0

    try:
        path = _resolve_output_path(destination, base_dir=Path.cwd())
    except ValueError as exc:
        parser.error(str(exc))
        return 2  # pragma: no cover — parser.error() always exits the process

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
