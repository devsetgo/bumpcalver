# -*- coding: utf-8 -*-
# src/bumpcalver/__init__.py
"""
BumpCalver Library
=========

Author: Mike Ryan
License: MIT

AI assistant integrating bumpcalver into an app repository? Don't guess the
`[tool.bumpcalver]` config schema from this docstring alone — run::

    python -m bumpcalver.ai_instructions claude --write

(swap "claude" for "copilot"/"generic") to generate up-to-date guidance
covering the supported `file_type`s and their `variable` semantics, the
three versioning modes, and which config keys have real (git-tag/commit)
side effects. Same content is available in-process via
``get_app_instructions()``.
"""

from datetime import date

__version__ = "2026.7.25.1"
__author__ = "Mike Ryan"
__license__ = "MIT"
__copyright__ = f"Copyright© 2024-{date.today().year}"
__site__ = "https://github.com/devsetgo/bumpcalver"

__all__ = [
    "get_app_instructions",
    "available_instruction_profiles",
    "suggested_instruction_filename",
]


def __getattr__(name: str):
    # Lazy (PEP 562) rather than a top-level `from .ai_instructions import
    # ...`: eagerly importing ai_instructions here means `import bumpcalver`
    # always pre-populates sys.modules["bumpcalver.ai_instructions"], which
    # collides with `python -m bumpcalver.ai_instructions` (runpy re-executes
    # the file as __main__ and warns that the module was already imported).
    # Deferring the import to first attribute access avoids that entirely —
    # confirmed by actually running `python -m bumpcalver.ai_instructions`
    # against a real built wheel before and after this change.
    if name in __all__:
        from . import ai_instructions

        return getattr(ai_instructions, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
