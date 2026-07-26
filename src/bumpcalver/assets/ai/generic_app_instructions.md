# Generic AI assistant instructions for apps using bumpcalver

Goal: correctly configure `bumpcalver` in an application repository —
authoring its `[tool.bumpcalver]` config and choosing the right CLI
invocation — without reverse-engineering the library's internals.

`bumpcalver` is a CLI/config-driven tool, not a library your code imports
and calls. "Integration" here means: get the config block right, pick the
correct `file_type` for every file that carries a version string, and pick
exactly one versioning mode.

## Setup: from zero to a working config

Follow this order — skipping steps (especially the "seed an initial version"
step) is the most common way a first setup silently does nothing.

### 1. Install

```bash
pip install bumpcalver
# or add "bumpcalver" to the project's dev dependencies
```

### 2. Decide where the config lives

- **If the project already has a `pyproject.toml`** (almost always true for
  a Python package): add a `[tool.bumpcalver]` table to it. This is the
  default choice.
- **If there is no `pyproject.toml`**, or the project's owner wants
  bumpcalver config kept separate: create a standalone `bumpcalver.toml` in
  the project root instead.
- If **both** exist in the same directory, bumpcalver uses `pyproject.toml`
  and ignores `bumpcalver.toml` — never create both and expect the second
  one to matter.

⚠️ **The two files use different key nesting — this is a real, easy-to-miss
trap:**

| In `pyproject.toml` | In standalone `bumpcalver.toml` |
|---|---|
| `[tool.bumpcalver]` table | keys at the **top level** of the file |
| `[[tool.bumpcalver.file]]` | `[[file]]` |

Writing `[[tool.bumpcalver.file]]` inside a standalone `bumpcalver.toml`
does not error — it just silently produces an empty file list, because
`bumpcalver.toml` is parsed flat (no `tool.bumpcalver` nesting expected). If
nothing gets updated after a `--build`, check this first.

### 3. Seed an initial version string in every target file

**bumpcalver finds and replaces an existing version string — it does not
create files or insert a new key.** Before writing any config, make sure
every file you intend to list already contains a literal version value in
the right shape, e.g.:

- Python: `__version__ = "2024.01.01"`
- TOML (`pyproject.toml` itself): `version = "2024.01.01"` under `[project]`
- JSON: `"version": "2024.01.01"` as a top-level key
- Dockerfile: `ARG VERSION=2024.01.01` and/or `ENV APP_VERSION=2024.01.01`

If a file is missing the key entirely, bumpcalver's update for that file
will fail (prints a "not found" message, doesn't write, doesn't error the
whole run) — that's a config/file mismatch to fix, not something bumpcalver
will fix for you.

### 4. Identify every file that needs updating, and map each to the table below

Walk the repo (or ask the user) for every file that carries this project's
version: the package's own version attribute, `pyproject.toml`'s
`project.version`, a Dockerfile `ARG`/`ENV`, a `package.json`-style file, a
docs page, etc. For each one, look up `file_type` in the table in the next
section and write one `[[tool.bumpcalver.file]]` (or `[[file]]`) block.

### 5. Choose `version_format`, `date_format`, `timezone`

If unsure, these are sane, verified defaults:

```toml
version_format = "{current_date}.{build_count:03}"
date_format = "%Y.%m.%d"
timezone = "America/New_York"
```

(`{current_date}` uses whatever `date_format` you set; `{build_count:03}`
zero-pads to 3 digits and only applies with `--build` — see "Versioning
modes" below for the full placeholder set including hybrid semver.)

### 6. Decide `git_tag` / `auto_commit`, and set them explicitly

Default to `false` for both unless the user explicitly asked for git
automation — see "Security / side-effect contract" below for why.

### 7. Add the `.gitignore` entries (see the dedicated section below)

### 8. Verify before the first real run

Always run `bumpcalver --dry-run` (add `--build` too if using build-count or
hybrid mode) immediately after writing the config, **before** running it for
real. It prints exactly what would change without writing anything:

```
[dry-run] Would bump version to 2024.01.02.001 in:
[dry-run]   src/mypkg/__init__.py
[dry-run]   pyproject.toml
```

If instead it prints `No files specified in the configuration.`, the config
wasn't found or parsed — check step 2's nesting trap first. If a file you
expected is missing from the list, check step 3 (the file's current content
doesn't match `variable`/`pattern`).

### Minimal working example (single file)

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:03}"
date_format = "%Y.%m.%d"
timezone = "America/New_York"
git_tag = false
auto_commit = false

[[tool.bumpcalver.file]]
path = "src/mypkg/__init__.py"
file_type = "python"
variable = "__version__"
```

### Typical Python package (multiple files, the common real-world case)

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:03}"
date_format = "%Y.%m.%d"
timezone = "America/New_York"
git_tag = true
auto_commit = false

[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "src/mypkg/__init__.py"
file_type = "python"
variable = "__version__"
version_standard = "python"
```

Run `bumpcalver --build --dry-run` against this, confirm the preview looks
right, then drop `--dry-run` to apply it for real.

## Completion contract (always deliver all items)

1. A `[tool.bumpcalver]` table in `pyproject.toml` (or a standalone
   `bumpcalver.toml`) with `version_format`, `date_format`, and `timezone`.
2. One `[[tool.bumpcalver.file]]` block **per file that carries a version
   string**, with the correct `file_type` and the matching
   `variable`/`directive`/`pattern` for that format (see the table below —
   these are not interchangeable).
3. Exactly one versioning mode, chosen deliberately (see "Versioning modes").
4. If pre-release suffixes (`--beta`/`--rc`/`--release`/`--custom`) are
   needed, the corresponding `beta_format`/`rc_format`/`release_format` keys.
5. An explicit statement of whether `git_tag`/`auto_commit` are enabled, and
   that enabling them causes a **real git commit and tag** — not a preview.
6. `.bumpcalver/` and `bumpcalver-history.json` added to `.gitignore`.
7. A short explanation of any non-obvious `file_type`/`variable` mapping choice.

## Supported file types (as of this bumpcalver version)

| `file_type` | `variable` means | Notes |
|---|---|---|
| `python` | Python variable name, e.g. `__version__` | Regex substitution |
| `toml` | **Dot-separated path**, e.g. `project.version` | Style-preserving (comments/order survive) |
| `yaml` | **Dot-separated path**, e.g. `configuration.version` | Style-preserving (comments/order survive) |
| `json` | **Plain top-level key**, e.g. `version` — NOT a dot path | Nested keys are not supported |
| `xml` | `ElementTree.find()` path, e.g. `version` or `metadata/version` | See XML caveat below |
| `dockerfile` | Variable name | **Requires `directive = "ARG"` or `"ENV"`** |
| `makefile` | Makefile variable name, e.g. `APP_VERSION` | |
| `properties` | `KEY` in a `KEY=value` file | |
| `env` | `KEY` in a `KEY=value` file (`.env`) | Quotes are stripped on read |
| `setup.cfg` | Dot path (`metadata.version`) or a simple key | |
| `text` | Not used — the whole file *is* the version | For a bare `VERSION` file |
| `regex` | Any key name | **Requires `pattern`**: a regex with exactly one capture group around the version |

Third-party file types can be added via the `bumpcalver.handlers` entry-point
group without forking bumpcalver — see the plugin-authoring guide if a
project needs a format not in this table.

**Do not confuse `json`'s plain top-level key with `toml`/`yaml`'s dot path**
— they look similar but are different mechanisms. Using a dot path for a
JSON file's `variable` will silently fail to find the key.

## Versioning modes — pick exactly one

These are different mechanisms, not variations of one setting. Picking the
wrong one silently produces a version scheme the developer didn't ask for.

1. **Plain calendar** (default): `version_format` uses only `{current_date}`.
   Every invocation produces a fresh date-based version.
2. **Calendar + build count**: `version_format` includes `{build_count}`
   (optionally `{build_count:03}` for zero-padding) and the CLI is invoked
   with `--build`. The build count increments only when invoked again on
   the same date; a new date resets it to 1.
3. **Hybrid semver + calendar**: `version_format` includes `{major}`,
   `{minor}`, and/or `{patch}` alongside `{current_date}`/`{build_count}`,
   and the config has integer `major`/`minor`/`patch` keys. Bump the
   semantic prefix with `--bump major|minor|patch` (this both increments the
   value in config and persists it back to the config file — a real write).

## Constraints vs. cosmetic — do not confuse these

- `version_standard = "python"` on a `[[tool.bumpcalver.file]]` block is
  **enforced**: it PEP-440-normalizes the version string before writing it
  (e.g. strips leading zeros, converts separators). Any other value (or
  omitting the key) is a no-op passthrough.
- **`file_type` is never validated against the file's actual content.**
  Nothing stops a config from setting `file_type = "python"` on a Ruby file
  — if the regex happens to match `__version__ = "..."`-shaped text it will
  "work" by coincidence, not because Ruby is a supported format. For a
  non-Python `KEY = "value"`-style file, use `file_type = "regex"` with an
  explicit `pattern` instead of borrowing an unrelated handler.

## Known limitation

`xml`'s `update_version` preserves the `<?xml ?>` declaration and comments
nested *inside* the root element, but comments in the XML **prolog** (before
the root element's opening tag) are dropped on write — a structural
`ElementTree` limitation, not a bug. Flag this if a target XML file has
prolog comments worth preserving.

## Security / side-effect contract

- `git_tag = true` and `auto_commit = true` cause `bumpcalver` to create a
  **real git tag** (and, with `auto_commit`, a **real commit**) on every
  successful run — not a dry-run or a suggestion. State explicitly which of
  these are enabled in any configuration you produce.
- `--dry-run` computes and prints what *would* change without writing
  anything or touching git — use it to preview a config before committing
  to it in CI.
- `--json` emits exactly one JSON object on stdout (log lines move to
  stderr) — the machine-readable way to capture the computed version, e.g.
  in a CI step: `` bumpcalver --build --json 2>/dev/null | jq -r '.version' ``.
- `--config-file PATH` (or `BUMPCALVER_CONFIG` env var) points at a config
  outside the current directory; file paths inside that config resolve
  relative to the config file's own directory, not the invoking cwd.
- `--undo`, `--undo-id`, and `--list-history` restore previous state from
  `.bumpcalver/backups/` + `bumpcalver-history.json` (both written to the
  current working directory). These flags are mutually exclusive with every
  version-bump option, including `--dry-run`, `--config-file`, and `--json`.

## `.gitignore` (always add this when configuring bumpcalver in a new repo)

```gitignore
# BumpCalver backup and history files
.bumpcalver/
bumpcalver-history.json
```

## Common mistakes to avoid

- Do not use a dot path for a `json` file's `variable` — it must be a plain
  top-level key.
- Do not set `file_type = "dockerfile"` without a `directive` — it's
  required, not optional.
- Do not set `file_type = "regex"` without a `pattern` — and the pattern
  must have exactly one capture group, or bumpcalver raises an error.
- Do not enable `git_tag`/`auto_commit` in an example/demo config without
  saying so explicitly — this is a real, not simulated, side effect.
- Do not combine `--dry-run`/`--config-file`/`--json` with
  `--undo`/`--undo-id`/`--list-history` — bumpcalver rejects this combination.
- Do not forget `.bumpcalver/` and `bumpcalver-history.json` in `.gitignore`.

## Prompt starters

"Set up bumpcalver for this Python package: bump `__version__` in
`src/mypkg/__init__.py` and `project.version` in `pyproject.toml` together,
using calendar + build count versioning, no git tagging."

"Add hybrid semver + calendar versioning to this repo: `major`/`minor`
starting at `1.0`, calendar suffix, git tag and commit enabled, and update
both `pyproject.toml` and a Dockerfile's `ARG VERSION`."
