# GitHub Copilot instructions for apps using bumpcalver

`bumpcalver` is a CLI/config-driven calendar-versioning tool — there is no
class or function to import and call from application code. Integration
means authoring a correct `[tool.bumpcalver]` config block and choosing the
right CLI invocation.

## Setup checklist (in order)

- [ ] **Install**: `pip install bumpcalver` (or add to dev dependencies).
- [ ] **Pick config location**: `pyproject.toml`'s `[tool.bumpcalver]` if
      the project has one (default choice); otherwise a standalone
      `bumpcalver.toml`. If both exist, `pyproject.toml` wins and
      `bumpcalver.toml` is ignored — never create both.
- [ ] ⚠️ **Nesting differs by file**: `pyproject.toml` uses
      `[tool.bumpcalver]` + `[[tool.bumpcalver.file]]`; standalone
      `bumpcalver.toml` is flat — top-level keys + `[[file]]`. Using the
      nested form in a standalone file silently produces an empty file list
      (no error).
- [ ] **Seed an initial version string** in every target file first —
      bumpcalver replaces an existing value, it does not create files or
      insert new keys. Missing key → that file's update silently fails
      (others still succeed).
- [ ] **List every file that carries a version** (package version
      attribute, `pyproject.toml`'s own `project.version`, Dockerfile
      `ARG`/`ENV`, etc.) as one `[[tool.bumpcalver.file]]`/`[[file]]` block
      each, using the reference table below.
- [ ] **Set `version_format`/`date_format`/`timezone`** — if unsure:
      `"{current_date}.{build_count:03}"` / `"%Y.%m.%d"` /
      `"America/New_York"`.
- [ ] **Set `git_tag`/`auto_commit` explicitly** — default `false` unless
      asked for git automation.
- [ ] **Add `.gitignore` entries** (below).
- [ ] **Verify with `bumpcalver --dry-run`** before a real run. Prints
      `No files specified in the configuration.` → recheck the nesting
      trap. Expected file missing from preview → recheck the seeded-version
      step.

### Minimal example

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

### Typical Python package

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

## Checklist (complete every item)

- [ ] `[tool.bumpcalver]` table added to `pyproject.toml`, or a standalone
      `bumpcalver.toml`, with `version_format`, `date_format`, `timezone`.
- [ ] One `[[tool.bumpcalver.file]]` block per file that carries a version
      string, each with the correct `file_type` and matching
      `variable`/`directive`/`pattern` (see table).
- [ ] Exactly one versioning mode chosen (plain calendar / calendar+build /
      hybrid semver+calendar) — not a mix.
- [ ] If pre-release suffixes are needed: `beta_format`/`rc_format`/
      `release_format` config keys added.
- [ ] `git_tag`/`auto_commit` values stated explicitly — `true` means a
      **real git tag/commit** on every run, not a preview.
- [ ] `.bumpcalver/` and `bumpcalver-history.json` added to `.gitignore`.

## `file_type` → `variable` reference table

| `file_type` | `variable` is... | Extra required key |
|---|---|---|
| `python` | a Python variable name, e.g. `__version__` | — |
| `toml` | a dot path, e.g. `project.version` | — |
| `yaml` | a dot path, e.g. `configuration.version` | — |
| `json` | a **plain top-level key** — not a dot path | — |
| `xml` | an `ElementTree.find()` path, e.g. `version` | — |
| `dockerfile` | a variable name | `directive` = `"ARG"` or `"ENV"` |
| `makefile` | a Makefile variable name | — |
| `properties` | a `KEY=value` key | — |
| `env` | a `.env` `KEY=value` key | — |
| `setup.cfg` | a dot path or simple key | — |
| `text` | not used (whole file is the version) | — |
| `regex` | any name | `pattern` = regex, exactly one capture group |

⚠️ **`json` and `toml`/`yaml` look similar but differ**: JSON's `variable`
is a plain top-level key, TOML/YAML's is a dot-separated path. Using a dot
path for JSON silently fails to find the key.

## Versioning modes (pick one)

1. **Plain calendar** (default) — `version_format` uses only `{current_date}`.
2. **Calendar + build count** — add `{build_count}` to `version_format`,
   invoke with `--build`.
3. **Hybrid semver + calendar** — add `{major}`/`{minor}`/`{patch}` to
   `version_format`, add integer `major`/`minor`/`patch` config keys, bump
   with `--bump major|minor|patch` (writes the new value back to config).

## Enforced vs. cosmetic

- `version_standard = "python"` → **enforced** PEP-440 normalization on write.
- `file_type` → **not validated** against the file's real content. A
  "working" mismatched `file_type` (e.g. `python` on a Ruby file) is
  coincidental regex overlap, not real support — use `file_type = "regex"`
  with an explicit `pattern` for unsupported `KEY = "value"` formats instead.

## Known limitation

`xml` drops comments in the prolog (before the root element opens) on
write — preserves the `<?xml ?>` declaration and comments nested inside the
root element. `ElementTree` structural limitation, not a bug.

## Side effects to call out explicitly

- `git_tag = true` / `auto_commit = true` — real git tag / real git commit.
- `--dry-run` — preview only, no writes, no git operations.
- `--json` — one JSON object on stdout, log lines move to stderr; use for
  CI: `bumpcalver --build --json 2>/dev/null | jq -r '.version'`.
- `--config-file PATH` / `BUMPCALVER_CONFIG` — config outside cwd; paths in
  it resolve relative to *its own* directory.
- `--undo` / `--undo-id` / `--list-history` — mutually exclusive with every
  version-bump flag (including `--dry-run`/`--json`/`--config-file`).

## `.gitignore` snippet

```gitignore
# BumpCalver backup and history files
.bumpcalver/
bumpcalver-history.json
```

## Common mistakes to avoid

- ❌ Dot path for a `json` file's `variable`.
- ❌ `dockerfile` entry missing `directive`.
- ❌ `regex` entry missing `pattern`, or a pattern without exactly one
  capture group.
- ❌ Enabling `git_tag`/`auto_commit` without flagging the real side effect.
- ❌ Combining `--dry-run`/`--json`/`--config-file` with the undo flags.
- ❌ Forgetting the `.gitignore` entries.

## Prompt starters

"Set up bumpcalver: bump `__version__` in `src/mypkg/__init__.py` and
`project.version` in `pyproject.toml` together, calendar + build count, no
git tagging."

"Add hybrid semver + calendar versioning: major/minor at 1.0, calendar
suffix, git tag and commit on, updating `pyproject.toml` and a Dockerfile's
`ARG VERSION`."
