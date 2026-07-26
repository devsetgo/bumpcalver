# tests/test_tooling_config.py
"""Regression tests that keep the dev-tooling config from re-fragmenting.

Ruff is the single tool for linting, import sorting, and formatting — these
assert that consolidation doesn't quietly drift back apart (e.g. someone
re-adding isort/black/flake8/autoflake as a "quick fix" for some new
complaint, recreating the exact overlap this was meant to remove).
"""

from pathlib import Path

import toml

REPO_ROOT = Path(__file__).resolve().parent.parent
RETIRED_TOOLS = {"autoflake", "autopep8", "black", "flake8", "isort", "pylint"}


def _load_pyproject():
    with open(REPO_ROOT / "pyproject.toml", "r", encoding="utf-8") as f:
        return toml.load(f)


def test_ruff_lint_has_isort_rules_enabled():
    config = _load_pyproject()
    ruff_lint = config["tool"]["ruff"]["lint"]
    assert "I" in ruff_lint["select"], (
        "Ruff's isort-equivalent rules ('I') should be enabled so ruff is the "
        "single tool responsible for import sorting."
    )


def test_no_standalone_isort_config_section():
    config = _load_pyproject()
    assert "isort" not in config.get("tool", {}), (
        "A [tool.isort] section duplicates ruff's own 'I' rules "
        "(see [tool.ruff.lint].select) and shouldn't coexist with them."
    )


def test_requirements_txt_has_no_retired_formatting_linting_tools():
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    declared_packages = {
        line.split("==")[0].split("#")[0].strip().lower()
        for line in requirements.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    overlap = declared_packages & RETIRED_TOOLS
    assert not overlap, (
        f"requirements.txt re-declares tool(s) {sorted(overlap)} that ruff "
        "already covers (lint + import-sort + format)."
    )
