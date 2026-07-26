# Claude instructions for apps using bumpcalver

You are configuring `bumpcalver`, a CLI/config-driven calendar-versioning
tool, in an application repository. This is not a library you import and
call from app code — the entire integration surface is a `[tool.bumpcalver]`
config block plus the `bumpcalver` CLI invocation. Do not guess the schema;
follow this contract.

## Setup procedure — follow in order

1. **Install**: `pip install bumpcalver` (or add to dev dependencies).
2. **Pick where the config lives**:
   - Project already has `pyproject.toml`? Add `[tool.bumpcalver]` to it.
     This is the default choice.
   - No `pyproject.toml`, or the user wants bumpcalver config separate?
     Create a standalone `bumpcalver.toml` in the project root.
   - If both exist, bumpcalver reads `pyproject.toml` and ignores
     `bumpcalver.toml` entirely — never create both.
   - **Nesting differs between the two** and this is a real trap: in
     `pyproject.toml` it's `[tool.bumpcalver]` + `[[tool.bumpcalver.file]]`;
     in standalone `bumpcalver.toml` it's flat — keys at the top level, and
     `[[file]]` (not `[[tool.bumpcalver.file]]`). Using the nested form in a
     standalone file doesn't error, it just silently produces an empty file
     list.
3. **Confirm every target file already has a version string to replace.**
   bumpcalver finds-and-replaces an existing value; it does not create
   files or insert a new key. If a file is missing the key, ask the user to
   seed one first (e.g. `__version__ = "2024.01.01"`) — don't assume
   bumpcalver will add it.
4. **Enumerate every file that carries a version** (package version
   attribute, `pyproject.toml`'s own `project.version`, Dockerfile
   `ARG`/`ENV`, etc.) and write one `[[tool.bumpcalver.file]]`/`[[file]]`
   block per file using the reference table below.
5. **Set `version_format`/`date_format`/`timezone`.** If unsure, use:
   `version_format = "{current_date}.{build_count:03}"`,
   `date_format = "%Y.%m.%d"`, `timezone = "America/New_York"`.
6. **Set `git_tag`/`auto_commit` explicitly** — default `false` unless the
   user asked for git automation (real side effect, see below).
7. **Add the `.gitignore` entries** (below).
8. **Verify with `bumpcalver --dry-run`** (add `--build` if using build
   count or hybrid mode) before running for real. It prints exactly what
   would change, e.g. `[dry-run] Would bump version to ... in: ...`. If it
   prints `No files specified in the configuration.`, re-check step 2's
   nesting. If an expected file is missing from the preview, re-check step 3.

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

### Typical Python package (the common real-world case)

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

## Completion contract

When asked to configure bumpcalver, deliver all of the following, not a
partial subset:

1. A `[tool.bumpcalver]` table in `pyproject.toml`, or a standalone
   `bumpcalver.toml` if the project doesn't want bumpcalver config mixed
   into `pyproject.toml` — with `version_format`, `date_format`, `timezone`.
2. One `[[tool.bumpcalver.file]]` block per file that carries a version
   string, each with the correct `file_type` for that file's real format
   (table below) and the matching `variable`/`directive`/`pattern`.
3. Exactly one versioning mode, chosen deliberately and stated in your
   response — see "Versioning modes."
4. `.bumpcalver/` and `bumpcalver-history.json` added to `.gitignore`.
5. If `git_tag`/`auto_commit` are set to `true`, say so explicitly in your
   response — these are real git operations, not previewed ones.

## File type reference

| `file_type` | `variable` semantics | Required extra keys |
|---|---|---|
| `python` | Python variable name (`__version__`) | — |
| `toml` | dot path (`project.version`) | — |
| `yaml` | dot path (`configuration.version`) | — |
| `json` | **plain top-level key only** — not a dot path | — |
| `xml` | `ElementTree.find()` path (`version`, `metadata/version`) | — |
| `dockerfile` | variable name | `directive = "ARG"` or `"ENV"` (mandatory) |
| `makefile` | Makefile variable name | — |
| `properties` | `KEY=value` key | — |
| `env` | `.env` `KEY=value` key | — |
| `setup.cfg` | dot path or simple key | — |
| `text` | none — whole file is the version | — |
| `regex` | any name | `pattern` (mandatory, exactly one capture group) |

If a target file's format isn't in this table, do not force-fit
`file_type = "python"` or another close-enough handler onto it just because
its regex happens to match — that's coincidental, not supported, behavior
(see "Enforced vs. coincidental" below). Prefer `file_type = "regex"` with
an explicit `pattern` for `KEY = "value"`-style files (Ruby, Rust, Go,
Java, etc.), or point the user at bumpcalver's `bumpcalver.handlers`
entry-point plugin mechanism if they want a real, reusable handler for their
own tooling.

## Versioning modes — pick exactly one, and say which one you picked

1. **Plain calendar** (default) — `version_format` uses only
   `{current_date}`.
2. **Calendar + build count** — `version_format` includes `{build_count}`
   (e.g. `{build_count:03}`), CLI invocation uses `--build`.
3. **Hybrid semver + calendar** — `version_format` includes `{major}`/
   `{minor}`/`{patch}`, config has integer `major`/`minor`/`patch` keys, and
   `--bump major|minor|patch` bumps the semantic prefix (this writes the new
   value back into the config file — a real, persistent change).

Do not mix these up: adding `{build_count}` to a hybrid `version_format`
without also documenting `--build` usage, or vice versa, produces a config
that silently behaves differently than the developer expects.

## Enforced vs. coincidental — the trap to avoid

`version_standard = "python"` is enforced: bumpcalver PEP-440-normalizes the
version string on write. Everything else about `file_type` matching is
**not validated** — bumpcalver will happily run a Python-file regex against
a Ruby file and "succeed" if the text shape happens to match. Do not present
that coincidence as intentional support for a format bumpcalver doesn't
actually have a handler for.

## Known, permanent limitation

XML comments in the prolog (before the root `<element>` opens) are dropped
on `update_version` — an `ElementTree` structural limitation. Comments
nested inside the root element, and the `<?xml ?>` declaration, are
preserved. Mention this if the target XML file has prolog comments.

## Side effects — state these explicitly in your response

- `git_tag = true` / `auto_commit = true` → real git tag / real git commit
  on every successful bump. Not a preview.
- `--dry-run` → preview only, writes nothing, no git operations.
- `--json` → single JSON object on stdout, all log lines on stderr. Use for
  CI: `` bumpcalver --build --json 2>/dev/null | jq -r '.version' ``.
- `--config-file PATH` / `BUMPCALVER_CONFIG` env var → use a config outside
  the cwd; file paths inside it resolve relative to *that file's* directory.
- `--undo` / `--undo-id` / `--list-history` → reads/restores from
  `.bumpcalver/backups/` + `bumpcalver-history.json` in the cwd. Mutually
  exclusive with every version-bump flag, including `--dry-run`/`--json`/
  `--config-file`.

## `.gitignore` — add whenever you configure bumpcalver in a repo that doesn't already have it

```gitignore
# BumpCalver backup and history files
.bumpcalver/
bumpcalver-history.json
```

## Common mistakes to avoid

- Using a dot path for `json`'s `variable` (it must be a plain top-level key).
- Omitting `directive` on a `dockerfile` entry.
- Omitting `pattern` on a `regex` entry, or writing a pattern with more/fewer
  than one capture group.
- Silently enabling `git_tag`/`auto_commit` without telling the user this
  produces real repository state changes.
- Suggesting `--dry-run` (or `--json`/`--config-file`) alongside
  `--undo`/`--undo-id`/`--list-history` — bumpcalver rejects that combination.
- Forgetting `.gitignore` entries for `.bumpcalver/`/`bumpcalver-history.json`.

## Prompt starters

"Configure bumpcalver for this repo: bump `__version__` in
`src/mypkg/__init__.py` and `project.version` in `pyproject.toml` together,
calendar + build count, no git tagging."

"Add hybrid semver + calendar versioning: major/minor starting at 1.0,
calendar build suffix, git tag and commit enabled, updating both
`pyproject.toml` and a Dockerfile's `ARG VERSION`."
