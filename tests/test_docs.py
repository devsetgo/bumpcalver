# tests/test_docs.py
"""Regression tests that keep checked-in documentation in sync with the code.

Unlike most of the test suite, these tests assert about *documentation*
content — the point is to fail loudly when a doc page silently drifts out of
sync with the thing it describes (e.g. a CLI option gets added/renamed/removed
without the docs being regenerated to match).
"""

import re
from pathlib import Path

from click.testing import CliRunner
from src.bumpcalver.cli import main

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


def _extract_help_block(markdown_text: str) -> str:
    """Extract the contents of the first ```text fenced code block."""
    match = re.search(r"```text\n(.*?)\n```", markdown_text, re.DOTALL)
    assert match, "Expected a ```text fenced code block in docs/cli-reference.md"
    return match.group(1)


def test_cli_reference_matches_help_output():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"], prog_name="bumpcalver")
    assert result.exit_code == 0

    live_help = result.output.rstrip("\n")
    documented_help = _extract_help_block(
        (DOCS_DIR / "cli-reference.md").read_text(encoding="utf-8")
    ).rstrip("\n")

    assert documented_help == live_help, (
        "docs/cli-reference.md is out of sync with `bumpcalver --help`. "
        "Regenerate the fenced code block from CliRunner().invoke(main, "
        "['--help'], prog_name='bumpcalver').output."
    )


def test_cli_reference_mentions_every_option():
    # Belt-and-suspenders companion to the exact-match test above: even if the
    # fenced block's *formatting* were hand-edited to still match by coincidence,
    # this independently confirms every declared option name is documented.
    documented = (DOCS_DIR / "cli-reference.md").read_text(encoding="utf-8")
    for param in main.params:
        for opt in getattr(param, "opts", []) + getattr(param, "secondary_opts", []):
            assert opt in documented, f"CLI option '{opt}' is missing from docs/cli-reference.md"
