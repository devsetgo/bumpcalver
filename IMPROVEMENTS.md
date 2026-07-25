# BumpCalver — Improvement Opportunities

Review date: 2026-07-25
Scope: `src/bumpcalver/`, `tests/`, `docs/`, tooling/CI config.

Baseline observed while reviewing: 302 tests pass, 99% line coverage, `ruff check` clean.
The codebase is in good shape overall — the gaps below are refinements, not fire drills.

---

## 1. Performance

1. ✅ **DONE (2026-07-25) — Redundant version reads per file per invocation.** In `cli.py`,
   `main()` read each file's current version up to twice: once implicitly via
   `get_build_version` (for `file_configs[0]` only), again to compute `current_raw_version`
   for pre-release suffixing (was cli.py:182-191), and again for every file in the no-op
   guard loop (was cli.py:204-225). A fresh `get_version_handler(...)` instance was also
   constructed each time. Fixed by adding `_read_current_version()` plus a per-invocation
   cache in `main()` keyed on `(path, variable, directive)` — see
   [cli.py:51-61](src/bumpcalver/cli.py#L51-L61) and
   [cli.py:186-192](src/bumpcalver/cli.py#L186-L192). The cache key deliberately includes
   `variable`/`directive`, not just `path`, so files with multiple entries (e.g. a Dockerfile
   with separate ARG/ENV directives) don't share a stale read. Verified with the full test
   suite (302 passed, coverage unchanged at 99%) and a live smoke test against a scratch
   project with a dual-directive Dockerfile config.

2. ✅ **DONE (2026-07-25) — Un-cached regex compilation in the version-parsing hot path.**
   `_clean_version_suffixes` and `_parse_hybrid_version` compiled regex patterns on every
   call via `re.sub`/`re.escape`/`re.fullmatch` rather than precompiling. Fixed: the
   suffix-stripping patterns are now module-level precompiled `re.Pattern` objects
   ([utils.py:142-150](src/bumpcalver/utils.py#L142-L150)), and the hybrid-format pattern
   builder is extracted into `_compile_hybrid_pattern()` and memoized with
   `functools.lru_cache` per `(version_format, date_format)` pair
   ([utils.py:99-124](src/bumpcalver/utils.py#L99-L124)), so repeated/bulk parsing against
   the same config no longer rebuilds and recompiles the same regex string. Verified with the
   full test suite (302 passed).

3. **Deferred — Full-file rewrites for structured formats.** `TomlVersionHandler.update_version`
   ([handlers.py:371-418](src/bumpcalver/handlers.py#L371-L418)) and
   `YamlVersionHandler.update_version` ([handlers.py:463-500](src/bumpcalver/handlers.py#L463-L500))
   parse the entire file into memory and re-serialize it from scratch to change a single
   scalar. For small config files this is irrelevant, but it's also the root cause of the
   correctness issues in §2 below (comment loss, key reordering) — switching to a
   surgical/regex-based update (like `PythonVersionHandler` already does) or a
   format-preserving library would fix both the performance profile and the data-loss risk
   in one change. **Intentionally not done in this pass** — it's really the same fix as
   Refactoring §2.1/§2.2 (needs `sort_keys=False` and a new `tomlkit` dependency), so it's
   tracked there instead of here to avoid doing it twice.

---

## 2. Refactoring Opportunities

1. **`YamlVersionHandler.update_version` silently reorders every key alphabetically.**
   `yaml.safe_dump(data, f)` at [handlers.py:495](src/bumpcalver/handlers.py#L495) defaults
   to `sort_keys=True`. I verified this directly:

   ```python
   >>> yaml.safe_dump({'z_key': 1, 'a_key': 2, 'configuration': {'name': 'app'}})
   a_key: 2
   configuration:
     name: app
   z_key: 1
   ```

   Any YAML file bumped by BumpCalver gets its top-level and nested keys resorted
   alphabetically, destroying the author's intended ordering/grouping. Fix: pass
   `sort_keys=False`. This is a correctness bug hiding inside what looks like a
   refactor-only concern, and it's currently untested (no test asserts key order is
   preserved — see Testing §4 below).

2. **`TomlVersionHandler.update_version` strips all comments on write.** The `toml` package
   has no comment/formatting model, so `toml.load` → mutate → `toml.dump` silently drops
   every comment in the file. Verified:

   ```python
   >>> toml.dumps(toml.loads('# top comment\n[tool.x]\nversion = "1.0"  # inline\n'))
   [tool.x]
   version = "1.0"
   ```

   Since this tool's primary target is `pyproject.toml` — a file that commonly carries
   comments — every bump against a commented `pyproject.toml` is destructive. Migrating to
   `tomlkit` (style-preserving, drop-in-ish replacement for the parts of the `toml` API used
   here) would fix this without changing the handler's public behavior.

3. **`XmlVersionHandler.update_version` drops the XML declaration and comments.**
   `tree.write(file_path)` at [handlers.py:640](src/bumpcalver/handlers.py#L640) doesn't
   pass `xml_declaration=True`, and `ElementTree.parse` doesn't preserve `<!-- comments -->`
   by default. Verified with a round-trip: a file with `<?xml version="1.0" encoding="UTF-8"?>`
   and a comment loses both after a single `update_version` call. Fix: parse with
   `ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))` (Python 3.8+) and write with
   `tree.write(file_path, xml_declaration=True, encoding="UTF-8")`, or move to `lxml` if
   broader XML fidelity is needed.

4. **`main()` in `cli.py` is a single ~215-line function** doing argument validation, config
   loading, semantic-version bumping, date/build versioning, pre-release suffixing, the
   no-op guard, backup creation, file updates, and git tagging/undo-history storage all in
   one place ([cli.py:79-295](src/bumpcalver/cli.py#L79-L295)). It's well covered by tests,
   but its size makes it hard to unit-test sub-behaviors in isolation (everything is
   exercised only through the full CLI). Extracting helpers such as
   `_read_current_version(file_config)`, `_compute_new_version(...)`, and
   `_all_files_already_updated(file_configs, new_version)` would let those pieces be tested
   directly and would remove the duplicated read-version logic between
   [cli.py:182-191](src/bumpcalver/cli.py#L182-L191) and
   [cli.py:211-218](src/bumpcalver/cli.py#L211-L218).

5. **Duplicated key=value parsing across handlers.** `PropertiesVersionHandler.read_version`
   ([handlers.py:826-847](src/bumpcalver/handlers.py#L826-L847)) and
   `EnvVersionHandler.read_version` ([handlers.py:867-890](src/bumpcalver/handlers.py#L867-L890))
   are near-identical (iterate lines, skip comments/blank lines, split on first `=`); only
   the `.env` variant additionally strips quotes. The base class already factors out the
   *write* side of this (`_update_key_value_file`,
   [handlers.py:221-242](src/bumpcalver/handlers.py#L221-L242)) — the same treatment could be
   applied to the read side.

6. **`import configparser` is repeated inside two methods** of `SetupCfgVersionHandler`
   ([handlers.py:922](src/bumpcalver/handlers.py#L922) and
   [handlers.py:997](src/bumpcalver/handlers.py#L997)) instead of once at module scope like
   every other stdlib import in the file.

7. **`MakefileVersionHandler.read_version` opens the file without an explicit encoding**
   ([handlers.py:774](src/bumpcalver/handlers.py#L774)): `open(file_path, "r")` instead of
   `open(file_path, "r", encoding="utf-8")`, which every other handler uses. On Windows
   (which is in the CI test matrix — `.github/workflows/testing.yml`) this defaults to the
   system locale encoding rather than UTF-8, so a Makefile with non-ASCII content could parse
   differently on Windows vs. Linux/macOS runners.

8. **`config.py` re-declares the same type annotation in both branches of an if/else**
   ([config.py:44](src/bumpcalver/config.py#L44) and
   [config.py:48](src/bumpcalver/config.py#L48)): `bumpcalver_config: Dict[str, Any] = ...`
   appears twice for the same variable. Harmless, but a lint/mypy run would flag the
   redundant annotation; only the first needs the type hint.

9. **Tooling overlap:** `ruff` is configured with a fairly complete lint ruleset but
   `select = ["I"]` (import sorting) is explicitly ignored in
   [pyproject.toml:148](pyproject.toml#L148) even though a separate `isort` config and
   `scripts/isort_run.sh` exist to do the same job, and `scripts/flake8.sh` /
   `scripts/autoflake.sh` duplicate checks `ruff` already covers. Consolidating onto `ruff`
   alone (enabling its `I` rules, dropping the standalone isort/flake8/autoflake scripts)
   would reduce the number of tools contributors need to install and keep in sync.

---

## 3. Documentation Improvements

1. **`docs/modules.md` is significantly stale** relative to the current API — this is the
   most impactful documentation gap found:
   - `main()` is documented with signature
     `main(beta: bool, build: bool, timezone: str, git_tag: bool, auto_commit: bool) -> None`
     ([docs/modules.md:198](docs/modules.md#L198)), but the real signature
     ([cli.py:79-92](src/bumpcalver/cli.py#L79-L92)) also has `rc`, `release`, `custom`,
     `undo`, `undo_id`, `list_history`, and `bump` — i.e. the undo/history feature and the
     hybrid semver `--bump` feature are entirely undocumented here.
   - `get_current_date()` and `get_current_datetime_version()` are documented without the
     `date_format` parameter ([docs/modules.md:11](docs/modules.md#L11),
     [docs/modules.md:41](docs/modules.md#L41)), and `get_current_date` is documented as
     "Raises: `ZoneInfoNotFoundError`" when the real implementation
     ([utils.py:308-316](src/bumpcalver/utils.py#L308-L316)) catches that exception
     internally and falls back to the default timezone instead of raising.
   - `get_build_version()` is documented with 3 parameters
     ([docs/modules.md:71](docs/modules.md#L71)); the real function
     ([utils.py:351-359](src/bumpcalver/utils.py#L351-L359)) takes 7
     (`date_format`, `major`, `minor`, `patch` are missing from the docs).
   This page should either be regenerated from the actual source (e.g. via `mkdocstrings`,
   which is already a project dependency per `requirements.txt` and used elsewhere per
   `mkdocs.yml`) or removed in favor of the auto-generated API docs so it can't drift again.

2. **No auto-generated CLI reference.** The CLI options are hand-documented in both
   `README.md` and `docs/index.md` (kept in sync manually) and could instead be generated
   from the `click.Command` itself (e.g. via `mkdocs-click` or a small script that dumps
   `--help`), eliminating a second place where flags like `--bump`, `--undo-id`, or
   `--list-history` need to be kept current by hand.

3. **`docs/timezones.md` is 3,071 lines** of what appears to be a generated reference table,
   checked directly into the docs source. A generated `timezones_table.html` already exists
   alongside it (`docs/timezones_table.html`), suggesting duplication of the same data in two
   formats. Consider generating both at build time from `zoneinfo`'s available zones rather
   than committing the large Markdown table, or collapsing the Markdown page to link to the
   HTML table instead of repeating the content.

4. **No contributor-facing extension guide** for adding a new file-type handler. The handler
   registry pattern (`_HANDLER_REGISTRY` in
   [handlers.py:1016-1027](src/bumpcalver/handlers.py#L1016-L1027)) is simple and easy to
   extend, but nothing in `CONTRIBUTING.md` or `docs/development-guide.md` walks through
   "how do I add support for a new file type" (subclass `VersionHandler`, implement
   `read_version`/`update_version`, register in `_HANDLER_REGISTRY`). This is exactly the
   kind of contribution the project says it welcomes (`CONTRIBUTING.md` invites people to
   "Add or improve a function"), so documenting the extension point would lower the barrier.

5. **Handler docstrings are heavily repetitive** — nearly every `read_version`/
   `update_version` method in `handlers.py` repeats the same `Args`/`Returns`/`Raises`
   boilerplate inherited from the abstract base class
   ([handlers.py:34-63](src/bumpcalver/handlers.py#L34-L63)). This isn't wrong, but it adds
   ~500 lines of near-duplicate text that must be kept consistent by hand; relying on the ABC
   docstring plus a one-line per-format note would be easier to maintain.

---

## 4. Testing

Coverage is already excellent (99% line coverage, 302 passing tests), so these are
targeted gaps rather than a broad call for "more tests."

1. **No regression test for YAML key ordering or TOML/XML comment preservation** — which is
   exactly how the bugs in Refactoring §2.1–2.3 went unnoticed. Adding a test that round-trips
   a YAML file with intentionally unsorted keys (asserting order is preserved after
   `update_version`), a commented `.toml` file (asserting the comment survives), and an XML
   file with a declaration/comment (asserting both survive) would both catch today's bugs and
   prevent regressions once fixed.

2. **The last few uncovered lines are exactly the exception-handling paths most worth
   testing directly:**
   - [cli.py:187, 190-191](src/bumpcalver/cli.py#L187-L191) — the `try/except Exception: pass`
     around reading `current_raw_version` for `--beta`/`--rc`/`--release`. There's no test
     exercising what happens when the *first* file config's handler raises while computing a
     pre-release suffix (e.g. malformed source file).
   - [utils.py:132-133](src/bumpcalver/utils.py#L132-L133) — the `except (IndexError,
     ValueError): count = 0` branch inside `_parse_hybrid_version`. Worth a direct unit test
     of `_parse_hybrid_version` with input that matches the pattern but has a non-numeric or
     missing `build_count` group.

3. **No type-checking gate in CI.** The codebase uses type hints extensively
   (`Dict[str, Any]`, `Optional[str]`, etc.) but nothing verifies they're internally
   consistent — `mypy`/`pyright` isn't in `requirements.txt`, `pyproject.toml`, or
   `.pre-commit-config.yaml`. Adding a `mypy` step (even permissive, e.g.
   `--ignore-missing-imports`) to `.github/workflows/testing.yml` and pre-commit would catch
   bugs like the duplicate-annotation redeclaration in `config.py` (§2.8) and any future
   signature drift between callers and handlers.

4. **No Windows-specific content test** for the Makefile encoding gap (Refactoring §2.7) —
   given Windows is already in the CI matrix, a test writing a Makefile with non-ASCII
   content and reading it back would catch the missing `encoding="utf-8"` before it causes a
   flaky Windows-only failure.

5. **Version-parsing regex machinery would benefit from property-based tests.**
   `parse_version` / `_parse_hybrid_version` / `_clean_version_suffixes`
   ([utils.py:86-305](src/bumpcalver/utils.py#L86-L305)) implement a fairly intricate
   format-string-to-regex translation. The existing tests (`test_calver_comprehensive.py`,
   `test_hybrid_versioning.py`) cover specific known formats well, but a `hypothesis`-based
   test that generates random `date_format`/`version_format` combinations and asserts
   `parse_version(version_format.format(...))` round-trips correctly would give much broader
   coverage of this logic's edge cases for comparatively little test code.

---

## 5. Capability Expansion Opportunities

1. **No "generic"/plain-text version handler.** Several of the example files in `examples/`
   (`version.txt`, `version.rb`) aren't actually covered by a dedicated handler — `version.rb`
   (`VERSION = "..."` inside a Ruby module) happens to match the *Python* handler's regex
   only because that regex is generic key = "value" matching, not because there's real Ruby
   support; there's no handler for a bare version file containing only the version string
   with no key at all (e.g. a plain `VERSION` file used by many shell-based release
   pipelines). A `"text"`/`"raw"` file type that reads/overwrites the entire file content
   verbatim, plus an explicitly generic `"regex"` handler with a user-supplied pattern for
   arbitrary `KEY = value`-style languages (Ruby, Rust `const`, Go, Java), would close this
   gap and make the mislabeled "python" handler usage for non-Python files unnecessary.

2. **No plugin/entry-point mechanism for custom handlers.** `_HANDLER_REGISTRY`
   ([handlers.py:1016-1027](src/bumpcalver/handlers.py#L1016-L1027)) is a plain module-level
   dict, so supporting a new/proprietary file format currently requires forking the project.
   Supporting registration via Python entry points (`importlib.metadata.entry_points`) would
   let third parties ship their own `VersionHandler` without modifying `bumpcalver` itself —
   a natural fit given the handler class hierarchy is already clean and abstract.

3. **No `--dry-run` flag.** The CLI already computes the no-op guard (whether files would
   change) before writing anything ([cli.py:204-229](src/bumpcalver/cli.py#L204-L229)); a
   `--dry-run` option that reuses that computation to print the version that *would* be
   written (and to which files) without touching disk or git would be a small addition with
   clear user value, especially in CI pipelines that want to preview a bump before committing
   to it.

4. **No way to point at a config file outside the CWD.** `load_config()`
   ([config.py:29-85](src/bumpcalver/config.py#L29-L85)) only ever looks for
   `pyproject.toml`/`bumpcalver.toml` in the current working directory. A `--config-file`
   CLI flag (or `BUMPCALVER_CONFIG` env var) would make the tool usable from monorepo tooling
   or wrapper scripts that invoke it from a different directory than the target project root.

5. **No machine-readable output mode.** All CLI output is `print()`-based prose
   (e.g. [cli.py:290-291](src/bumpcalver/cli.py#L290-L291)). A `--json` flag that emits the
   computed version, updated files, and operation ID as structured JSON would make it easier
   to consume `bumpcalver`'s output from other CI scripts without scraping stdout.

6. **Undo/backup storage is git-repo-root-relative only implicitly.** `BackupManager`
   defaults to `.bumpcalver/backups` and `bumpcalver-history.json` under `os.getcwd()`
   ([backup_utils.py:37-41](src/bumpcalver/backup_utils.py#L37-L41)). There's no `.gitignore`
   guidance or automatic entry ensuring `.bumpcalver/` and `bumpcalver-history.json` are
   excluded from version control by default (this repo's own `bumpcalver-history.json` is
   currently untracked-but-present at the repo root) — the tool could optionally offer to
   append these paths to `.gitignore` on first run, or document the recommended
   `.gitignore` entries prominently in the undo docs.

---

## 6. Add Packaged AI-Assistant Integration Instructions (final improvement)

This is the last item in this document by request — it's a separate initiative from §1–5
above rather than a fix to something broken. The goal is to port the pattern already shipped
in `pydantic-schemaforms` and `devsetgo_lib` (see `ADD_AI_INSTRUCTIONS.md` at the repo root
for the full, generic playbook this section instantiates): ship AI-assistant integration
instructions **as package data**, with a small API to read them and a CLI to bootstrap them
into a consuming project, so the guidance can never drift out of sync with the installed
version of `bumpcalver`.

`bumpcalver` differs from those two libraries in one important way worth calling out before
copying the playbook verbatim: it isn't a framework an app imports and builds on top of —
it's a CLI/config-driven tool. "Integration" here means "help a developer correctly author
the `[tool.bumpcalver]` config block and CLI invocation for their project," not "help them
call the right class/function in their own code." That changes the *content* of the
instruction files and the choice of regression-test anchor string, but not the mechanics
(module layout, packaging, discoverability hooks, security-hardened CLI) — those transfer
directly.

### 6.1 File layout

Adapted for this repo's existing `src/` layout:

```
src/bumpcalver/
├── ai_instructions.py
└── assets/
    └── ai/
        ├── generic_app_instructions.md
        ├── claude_app_instructions.md
        └── copilot_app_instructions.md
tests/
└── test_ai_instructions.py
```

### 6.2 Core module

Copy `ai_instructions.py` from `ADD_AI_INSTRUCTIONS.md` §2 verbatim, swapping
`<package_name>` → `bumpcalver`. No changes to the logic are needed — the profile
aliasing, `resources.files()` lookup, and the path-traversal-hardened `--output`/`--write`
CLI (`_resolve_output_path`) are all domain-independent and should be reused exactly,
including the security regression tests in §6.7 below.

### 6.3 Export from `__init__.py`

`src/bumpcalver/__init__.py` ([__init__.py:1-16](src/bumpcalver/__init__.py#L1-L16))
currently only defines version/author/license metadata and has no `__all__`. Add:

```python
from .ai_instructions import (
    available_instruction_profiles,
    get_app_instructions,
    suggested_instruction_filename,
)

__all__ = [
    "get_app_instructions",
    "available_instruction_profiles",
    "suggested_instruction_filename",
]
```

(This is also the first place `__all__` would be introduced in this file — worth doing
explicitly rather than relying on implicit export-everything behavior.)

### 6.4 Packaging

Unlike the playbook's generic setuptools/hatchling include-list guidance, `bumpcalver`'s
`[tool.hatch.build]` config ([pyproject.toml:155](pyproject.toml#L155)) already works from
an **exclude list**, not an allowlist — everything under `src/bumpcalver/` ships by default
unless it matches one of the excluded patterns (`*.json`, `tests/`, `__pycache__/`, etc.).
None of those patterns should catch `src/bumpcalver/assets/ai/*.md`, so no config change
should be required — but per the playbook's step 4, this must be *verified for real*, not
assumed:

```bash
python -m build
pip install --force-reinstall dist/bumpcalver-*.whl
python -c "from bumpcalver import get_app_instructions; print(len(get_app_instructions('claude')))"
```

### 6.5 Discoverability hooks

Two anchor points, matching the playbook's "top-level docstring + primary entry-point
docstring" rule:

- **`src/bumpcalver/__init__.py`** module docstring
  ([__init__.py:3-9](src/bumpcalver/__init__.py#L3-L9)) — currently 6 lines of bare
  metadata; extend with the pointer paragraph from playbook §5.
- **`src/bumpcalver/cli.py`** module docstring
  ([cli.py:1-33](src/bumpcalver/cli.py#L1-L33)) — this is the closest thing `bumpcalver` has
  to a "primary entry point," since the whole product surface is the `main()` CLI command.
  Add the two-line pointer from playbook §5 here rather than on a class, since there is no
  primary class.

### 6.6 Profile content — what actually needs to go in the `.md` files

This is the part that most diverges from the pydantic-schemaforms/devsetgo_lib versions,
since there's no "construct an object, call render()" pattern here. The completion contract
for each profile should instead walk an AI assistant through:

1. Add a `[tool.bumpcalver]` table (or a standalone `bumpcalver.toml`) with `version_format`,
   `date_format`, and `timezone`.
2. Add one `[[tool.bumpcalver.file]]` block **per file that carries a version string**, with
   the correct `file_type` (enumerate all 10 currently supported:
   `python`/`toml`/`yaml`/`json`/`xml`/`dockerfile`/`makefile`/`properties`/`env`/`setup.cfg`)
   and the matching `variable`/`directive` for that format.
3. Pick exactly one versioning mode and say why the others don't apply: plain calendar
   (default), calendar + build count (`--build`), or hybrid semver+calendar
   (`{major}.{minor}.{patch}` placeholders plus `--bump major/minor/patch`). These are
   different mechanisms, not variations of one setting — picking the wrong one silently
   produces a version scheme the developer didn't ask for.
4. Pre-release flags (`--beta`/`--rc`/`--release`/`--custom`) and their corresponding
   `beta_format`/`rc_format`/`release_format` config keys — the CLI already enforces these
   as mutually exclusive, so the instructions should say so rather than imply the assistant
   needs to add that validation itself.
5. `git_tag`/`auto_commit` — flag explicitly that enabling these causes a **real git commit
   and tag**, not a dry-run or preview, mirroring the playbook's "security/config contract"
   guidance (§6 of the playbook) for anything with a real side effect.
6. The undo/history system (`--undo`, `--undo-id`, `--list-history`) and that
   `.bumpcalver/backups/` + `bumpcalver-history.json` are written to the CWD and should be
   added to `.gitignore` (this ties directly into Capability Expansion §5.6 above).

**"Enforced vs. cosmetic" analog** (playbook §6/§10.3 calls this out as the single most
important section to get right): `version_standard = "python"` is *enforced* formatting —
it PEP-440-normalizes the version string at write time. By contrast, nothing in
`file_configs` validates that `file_type` actually matches the file's real format; picking
`file_type = "python"` for a non-Python file (e.g. a Ruby `VERSION = "..."` file) "works"
today only because the regex happens to match, not because it's real, supported Ruby
handling (see Capability Expansion §5.1 above). The instructions must say this explicitly so
an AI assistant doesn't recommend the coincidence as an intentional pattern.

**Known-limitations disclosure** (playbook §10.8, "don't overclaim"): until Refactoring
§2.1–2.3 above are fixed, the instructions must explicitly warn that running `bumpcalver`
against a YAML file reorders all of its keys alphabetically, and against a commented TOML or
XML file strips the comments (and, for XML, the `<?xml ?>` declaration). An AI assistant
recommending `bumpcalver` for those files needs to be able to pass that risk on to the
developer rather than silently omitting it. Once those bugs are fixed, this caveat should be
removed from the instructions in the same change — a direct instance of playbook lesson
§10.7 ("update instructions alongside API changes").

### 6.7 Tests

Adapt the playbook's test file (`ADD_AI_INSTRUCTIONS.md` §7) with one substitution: there is
no `<PrimaryEntryPoint>` class to assert on, so the content-regression test should instead
assert that a stable, load-bearing config token — e.g. `"[[tool.bumpcalver.file]]"` — appears
in the generic profile text. All of the CLI/plumbing tests and, critically, **all of the
path-traversal security regression tests** (`test_cli_output_flag_rejects_path_traversal_outside_cwd`,
`test_cli_output_flag_rejects_absolute_path_outside_cwd`,
`test_resolve_output_path_rejects_sibling_directory_with_shared_prefix`, etc.) should be
copied over unchanged — that logic is entirely domain-independent and the playbook is
explicit that these must not be skipped.

### 6.8 README section

Same template as playbook §8, commands adjusted to this package:

```bash
python -m bumpcalver.ai_instructions claude --write     # writes ./CLAUDE.md
python -m bumpcalver.ai_instructions copilot --write    # writes ./.github/copilot-instructions.md
python -m bumpcalver.ai_instructions generic > AI_INSTRUCTIONS.md
```

Place it in `README.md` near the existing `## Configuration` section, since that's the part
of the README this feature is effectively summarizing/automating.

### 6.9 Rollout checklist

Same 9 steps as playbook §11 (write module → write profile `.md` files and verify every
claim by running it → export from `__init__.py` → packaging + clean-venv verification →
discoverability docstrings → tests including security regressions → README section →
optional docs/demo page → standing rule to update the `.md` files alongside future config/CLI
changes). Given this is explicitly the last planned improvement for this pass, it's
reasonable to treat it as its own follow-up unit of work rather than interleaving it with
§1–5.

---

## Suggested Priority Order

If tackling incrementally, the highest-leverage fixes are:

1. Fix YAML key-reordering and TOML/XML comment/declaration loss (§2.1–2.3) — these are
   silent data-loss bugs, not just style issues.
2. Add the regression tests that would have caught them (§4.1).
3. Regenerate/fix `docs/modules.md` (§3.1) — it currently misrepresents the public API,
   including omitting the undo and hybrid-versioning features entirely.
4. Add `mypy` to CI (§4.3) and fix the Makefile encoding gap (§2.7) — cheap, durable
   correctness nets.
5. Everything else (dry-run, plugin handlers, generic text handler) is additive and can be
   prioritized against actual user requests.
