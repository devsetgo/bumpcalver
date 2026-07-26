# AI Assistant Instructions

BumpCalver ships app-integration guidance for AI assistants **as package
data** — the same guidance an assistant would otherwise have to
reverse-engineer from this documentation site, bundled directly with the
version of `bumpcalver` you actually installed, so it can never drift out of
sync with an externally copy-pasted snippet.

This isn't guidance for *using* bumpcalver's own source code — it's guidance
for an assistant helping a developer **configure bumpcalver in their own
project**: authoring the `[tool.bumpcalver]` config block, picking the right
`file_type` for each version-carrying file, and choosing one of the three
versioning modes.

## Quick start

```bash
python -m bumpcalver.ai_instructions claude --write     # writes ./CLAUDE.md
python -m bumpcalver.ai_instructions copilot --write    # writes ./.github/copilot-instructions.md
python -m bumpcalver.ai_instructions generic > AI_INSTRUCTIONS.md
```

Or in-process:

```python
from bumpcalver import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)

print(available_instruction_profiles())  # ('claude', 'copilot', 'generic')
print(get_app_instructions("claude"))
print(suggested_instruction_filename("claude"))  # "CLAUDE.md"
```

Aliases are accepted: `github-copilot` → `copilot`, `anthropic-claude` →
`claude`, `default` → `generic`.

See [API Reference](modules.md#ai-assistant-instructions) for the full
`get_app_instructions`/`available_instruction_profiles`/
`suggested_instruction_filename` signatures.

## CLI

```text
usage: python -m bumpcalver.ai_instructions [-h] [--write] [--output PATH]
                                             [profile]
```

- `profile` — one of `claude`/`copilot`/`generic` (or an alias); defaults to
  `generic`.
- `--write` — write to the profile's suggested destination file (`CLAUDE.md`,
  `.github/copilot-instructions.md`, or `AI_INSTRUCTIONS.md`) instead of
  stdout.
- `--output PATH` — write to an explicit path instead. `PATH` is validated
  to stay within the current working directory (see "Security" below) —
  this matters because the whole point of this CLI is that an AI assistant
  may invoke it directly, not just a human typing a path by hand.

## Full instructions by profile

The three sections below are the **exact, literal content** of the packaged
instruction files, generated into this page at build time from the same
`get_app_instructions()` the CLI and Python API serve — not a manually
copied snapshot that could drift out of sync with what
`python -m bumpcalver.ai_instructions <profile>` actually outputs.

### Generic

<!-- AI_INSTRUCTIONS:generic -->

### Claude

<!-- AI_INSTRUCTIONS:claude -->

### Copilot

<!-- AI_INSTRUCTIONS:copilot -->

## What these instructions cover

- A step-by-step setup procedure from a blank repo: install, decide between
  `pyproject.toml` and a standalone `bumpcalver.toml` (including the flat-vs-
  nested key trap between the two), seed an initial version string in every
  target file (bumpcalver replaces existing values, it does not create files
  or insert keys), map every file to a `file_type`, pick sane
  `version_format`/`date_format`/`timezone` defaults, and verify with
  `--dry-run` before a real run — plus copy-paste-ready minimal and
  "typical Python package" example configs, both verified against the real
  CLI.
- All 12 built-in `file_type`s and what `variable` means for each (a plain
  key vs. a dot path vs. an `ElementTree.find()` path — these are genuinely
  different mechanisms, not variations of one setting).
- The three versioning modes (plain calendar, calendar + build count,
  hybrid semver + calendar) and how to pick one.
- Pre-release suffix flags and their config keys.
- Which config keys have **real side effects** (`git_tag`/`auto_commit`
  create an actual git tag/commit, not a preview).
- `--dry-run`, `--json`, and `--config-file` for previewing, scripting, and
  monorepo/cross-directory use.
- The undo/backup system and the `.gitignore` entries a new bumpcalver
  integration should add.
- One permanent, structural limitation (XML prolog comments) worth knowing
  about up front.

## What these instructions do NOT cover

Being explicit about gaps matters more than it might seem — an AI assistant
reading documentation will trust silence as "not applicable," which is worse
than an honest "not covered yet":

- **The `bumpcalver.handlers` plugin/entry-point mechanism** for registering
  a custom `file_type` from a third-party package is mentioned in passing
  but not walked through step by step — see the
  [development guide](development-guide.md#distributing-your-handler-as-a-plugin)
  for the full recipe if a project needs a file format with no built-in or
  regex-compatible handler.
- **Undo internals** (backup file naming, `bumpcalver-history.json`'s exact
  schema) beyond "these two paths exist and should be gitignored" — see the
  [Undo documentation](undo.md) for the full mechanics.
- **CI/CD recipes** beyond the single `--json`/`jq` example already in the
  instructions — see the [CLI Reference](cli-reference.md#machine-readable-output-json)
  for the full `--json` payload shape per case.

## Security

`--output` is treated as untrusted input, not a trusted human-typed path —
the entire premise of this feature is that an AI assistant may invoke this
CLI directly, and a misdirected instruction, a reasoning bug, or a prompt
injection could produce an adversarial path argument. `_resolve_output_path`
resolves the destination (following symlinks) and rejects anything that
isn't a descendant of the current working directory, using `Path.parents`
containment rather than a string-prefix check (a prefix check would wrongly
treat a sibling directory like `project-evil/` as being inside `project/`).
This is covered by dedicated regression tests
(`tests/test_ai_instructions.py`) that must not be weakened or removed.

## Packaging

The three profile `.md` files ship as package data under
`bumpcalver/assets/ai/` — verified with a real `python -m build` +
install-into-a-clean-venv check, not just editable-mode testing, since
packaging misconfiguration is easy to miss in dev mode and only surfaces for
someone doing a real `pip install`.

## Keeping this in sync

If you're changing bumpcalver's public config schema (a new `file_type`, a
new CLI flag, a new config key with a real side effect), update
`src/bumpcalver/assets/ai/*.md` in the same change — the "Full instructions
by profile" section above regenerates from those files automatically at
`mkdocs build` time (via `scripts/mkdocs_hooks.py`), so there's no separate
docs-page edit to remember; editing the source files is the whole job.
A regression test
(`test_get_app_instructions_documents_every_builtin_file_type`) asserts
every `file_type` in `_HANDLER_REGISTRY` is mentioned in the generic
profile, but that only catches missing file types — it can't catch stale
prose about CLI flags or config keys, so this has to be a deliberate habit,
not something a test alone will enforce.
