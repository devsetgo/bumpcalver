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

3. ✅ **DONE (2026-07-26) — Full-file rewrites for structured formats: closed with real
   numbers, not left as an assumption.** `TomlVersionHandler.update_version` and
   `YamlVersionHandler.update_version` do still parse the entire file into memory and
   re-serialize it from scratch to change a single scalar (via `tomlkit` and, as of today,
   `ruamel.yaml` — see Refactoring §2.1's correction below for why YAML's migration was still
   outstanding until now). That part of the original write-up was accurate. What wasn't
   fully justified before was the claim that this is "low-impact" — I hadn't actually
   measured it. Benchmarked both today:
   - `TomlVersionHandler` against this repo's own real 175-line `pyproject.toml`: **8.5 ms**
     per update, averaged over 200 runs.
   - `YamlVersionHandler` against a realistic-sized config file (`examples/example.yaml`,
     14 lines): **1.8 ms** per update, averaged over 200 runs.
   - `YamlVersionHandler` against a deliberately pathological synthetic stress file (2,000
     lines, one interspersed comment per line — far larger and far more comment-dense than
     any real bumpcalver-managed config): **193 ms** per update, averaged over 50 runs.
     Comment-preserving parsing is the expensive part; a comment-free 2,000-line file is
     much cheaper, but that's not the realistic case worth optimizing for either way.
   Even the pathological case is a one-time cost in a CLI that runs once per invocation, not
   a hot loop — nowhere close to perceptible, let alone worth trading a well-tested
   format-preserving library for a hand-rolled surgical text-splice editor (which is exactly
   the kind of fragile, regex-shaped approach that caused the original data-loss bugs this
   tool used to have). Formally closing this as resolved rather than leaving it "deferred
   pending real-world evidence that never arrives" — the evidence now exists and says it
   doesn't matter at the file sizes this tool actually sees.

---

## 2. Refactoring Opportunities

1. ✅ **DONE (2026-07-25, key order; 2026-07-26, comments) — `YamlVersionHandler.update_version`
   silently reordered every key alphabetically, and separately, dropped every comment.**
   The 2026-07-25 fix (`sort_keys=False`) only ever addressed key ordering — I described it
   at the time as fixing "the data-loss risk" generally, which **overstated what it actually
   fixed**: `yaml.safe_load`/`yaml.safe_dump` round-trip through a plain dict, which has no
   comment model at all, so every comment was *still* being silently dropped on every write,
   regardless of `sort_keys`. This was only actually fixed on 2026-07-26, alongside
   Performance §1.3 below, by migrating the handler to `ruamel.yaml`'s round-trip mode (same
   pattern as the `tomlkit` migration in item 2 below — see that entry for why plain
   `PyYAML` can't do this and a hand-rolled surgical text editor isn't the right trade either).
   Regression tests in `tests/test_handlers.py`: `test_yaml_handler_update_version_preserves_key_order`
   (key order, real file, predates the ruamel.yaml migration and still passes under it) and
   `test_yaml_handler_update_version_preserves_comments` (comments, added with the migration) —
   both confirmed to fail against the pre-fix code before being confirmed to pass against it.

2. ✅ **DONE (2026-07-25) — `TomlVersionHandler.update_version` stripped all comments on
   write.** Migrated the handler from the plain `toml` package to `tomlkit` (style-preserving)
   — see [handlers.py:359-449](src/bumpcalver/handlers.py#L359-L449). `tomlkit` is now an
   explicit runtime dependency (`pyproject.toml`, `requirements.txt`); it was previously only
   present as a transitive dependency of `pylint`, so this would have broken on a real
   `pip install` of just the library. `config.py` still uses the plain `toml` package
   deliberately — it's read-only there (parsing `pyproject.toml`/`bumpcalver.toml` at
   startup), so it has no comment-loss risk and didn't need migrating. Regression test
   `test_toml_handler_update_version_preserves_comments` round-trips a real commented TOML
   file; I additionally smoke-tested against a real copy of this repo's own 175-line
   `pyproject.toml` and confirmed only the `version = "..."` line changed in the diff.

3. ✅ **DONE (2026-07-25) — `XmlVersionHandler.update_version` dropped the XML declaration
   and comments.** Fixed at [handlers.py:664-680](src/bumpcalver/handlers.py#L664-L680): parses
   with `ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))` and writes with
   `xml_declaration=True, encoding="UTF-8"`. This preserves the `<?xml ?>` declaration and
   comments nested *inside* the root element, but — verified empirically, and documented
   honestly in the class docstring rather than overclaiming — comments in the XML *prolog*
   (before the root element's opening tag) are still dropped; that's a structural
   `ElementTree` limitation (the tree model starts at the root element) that would need `lxml`
   to fully close. Regression test `test_xml_handler_update_version_preserves_declaration_and_comments`
   round-trips a real file with both a declaration and a nested comment.

4. ✅ **DONE (2026-07-25) — `main()` in `cli.py` was a single ~215-line function.** Extracted
   four standalone, independently-testable helpers:
   `_apply_semantic_bump`, `_compute_new_version`, `_all_files_already_updated`, and
   `_create_git_tag_and_commit` ([cli.py:64-184](src/bumpcalver/cli.py#L64-L184)), alongside
   the `_read_current_version` helper from the earlier performance pass. `main()` itself is
   now ~90 lines of orchestration. All 27 existing `CliRunner`-based integration tests in
   `tests/test_cli.py` pass unmodified — the extracted helpers reference the same
   module-level imported names `main()` always used, so the existing
   `mock.patch('src.bumpcalver.cli.X')`-style patches keep working. Added
   `tests/test_cli_helpers.py` (19 new tests) exercising each extracted piece directly,
   which is the whole point of the refactor: e.g. `_all_files_already_updated` and
   `_create_git_tag_and_commit`'s git-failure-is-swallowed behavior can now be tested without
   spinning up the full CLI.

5. ✅ **DONE (2026-07-25) — Duplicated key=value parsing across handlers.** Added
   `_read_key_value_file(file_path, variable, strip_quotes=False)` to the `VersionHandler`
   base class ([handlers.py:245-271](src/bumpcalver/handlers.py#L245-L271)), mirroring the
   existing shared write-side helper. `PropertiesVersionHandler.read_version` and
   `EnvVersionHandler.read_version` now both delegate to it (the `.env` variant passes
   `strip_quotes=True`). Covered by the existing Properties/Env test suite, which already
   exercised both the found/not-found and quote-stripping paths — handlers.py stayed at 100%
   coverage through this change.

6. ✅ **DONE (2026-07-25) — `import configparser` repeated inside two methods.** Moved to a
   single module-level import in `handlers.py` ([handlers.py:9](src/bumpcalver/handlers.py#L9)).

7. ✅ **DONE (2026-07-25) — `MakefileVersionHandler.read_version` opened the file without an
   explicit encoding.** Added `encoding="utf-8"` at
   [handlers.py:774](src/bumpcalver/handlers.py#L774). New regression test
   `test_makefile_handler_read_version_uses_explicit_utf8_encoding` asserts the `open()` call
   arguments directly (rather than just reading ASCII content back correctly, which would
   have passed even without the fix on this sandbox's own utf-8-default platform).

8. ✅ **DONE (2026-07-25) — `config.py` re-declared the same type annotation in both branches
   of an if/else.** Consolidated to a single annotation at
   [config.py:43](src/bumpcalver/config.py#L43).

9. **Not done — tooling overlap** (`ruff`'s `I` rule vs. standalone `isort`/`flake8`/`autoflake`
   scripts). Deliberately deferred: this is a dev-tooling/CI consolidation rather than library
   code, touches multiple scripts and `.pre-commit-config.yaml`, and is more of a project
   convention decision than a correctness fix — worth doing as its own separate, deliberate
   change rather than folding into this pass.

---

## 3. Documentation Improvements

1. ✅ **DONE (2026-07-25) — `docs/modules.md` was significantly stale.** Rather than
   hand-fixing the stale signatures, replaced the page entirely with `mkdocstrings`
   `:::` directives pulling live from the actual docstrings (see `docs/modules.md`), so it
   can't drift again by construction. This also surfaced that the page was orphaned —
   `mkdocs.yml`'s nav had it commented out under the *wrong filename*
   (`# - Modules: 'models.md'`, but the real file is `modules.md`) — so it wasn't even
   linked from the site navigation. Fixed the nav entry and added `paths: [src]` to the
   `mkdocstrings` python handler config, without which it can't import the src-layout
   package to introspect it. Also added docstrings to `get_current_date()`, and `main()`
   in `cli.py`, since mkdocstrings had nothing to render for them (that's why the old page
   showed `get_current_date` as raising `ZoneInfoNotFoundError` — someone was documenting
   from reading the code, since there was no docstring to pull from — the docs task itself
   is what made this bug-class visible). Verified with a real `mkdocs build --strict`; the
   only remaining warnings are 4 pre-existing ones unrelated to this page (a plugin-ordering
   warning and two broken links in `index.md`/`calendar-versioning-guide.md` that predate
   this session and weren't touched).

2. ✅ **DONE (2026-07-25) — No auto-generated CLI reference.** Rather than adding a new
   `mkdocs-click` dependency, added `docs/cli-reference.md` containing the literal,
   captured `bumpcalver --help` output, paired with a regression test
   (`tests/test_docs.py::test_cli_reference_matches_help_output`) that invokes
   `CliRunner().invoke(main, ["--help"])` and asserts it matches byte-for-byte, plus a
   companion test asserting every declared Click option string appears in the doc. I
   verified the test actually catches drift (not just passes trivially) by temporarily
   adding a fake `--dry-run` option to a scratch copy of `cli.py` and confirming both tests
   fail with a clear message, then restored the real file and confirmed a clean pass.

3. **Not done — `docs/timezones.md` is 3,071 lines, duplicating `timezones_table.html`.**
   Investigated rather than assumed: extracted and diffed the timezone sets from both
   files — 598 zones each, identical sets, no drift between them. So unlike items 1/2 this
   isn't a live bug, just static duplication of data that essentially never changes.
   Properly fixing it would mean building a real generate-at-build-time pipeline (a new
   mkdocs hook or pre-build script); given the low payoff versus that effort, deliberately
   deferring rather than doing a partial/risky job on a 3,000-line generated file.

4. **Correction, not a fix — the claimed missing contributor extension guide already
   existed.** On inspection, `docs/development-guide.md`'s existing "File Format Support"
   section (under "Adding New Features") already walked through subclassing
   `VersionHandler`, registering in `_HANDLER_REGISTRY`, and adding tests — my original
   review claim that "nothing... walks through this" was wrong, and I'm correcting the
   record here rather than claiming credit for writing something that already existed.
   What *was* missing, and what I actually added: the existing guide's example was a
   generic `# Implementation` stub with no mention of the base class's real shared helpers
   (`_read_key_value_file`/`_update_key_value_file`/`_handle_regex_update`, added/
   discovered during the Refactoring pass in §2). Replaced the stub with a real,
   **verified-by-actually-running-it** `IniVersionHandler` example reusing
   `_read_key_value_file`/`_update_key_value_file`, and a verified-working test example
   using `tmp_path` instead of mocks (matching the pattern the YAML/TOML/XML regression
   tests already established). Also linked the guide from the `VersionHandler` base-class
   docstring so it's discoverable from the generated API reference too.

5. ✅ **DONE (2026-07-25) — Handler docstrings were heavily repetitive.** Condensed every
   concrete handler class's docstring and every `read_version`/`update_version` override
   in `handlers.py` from the repeated `Args`/`Returns`/`Raises` boilerplate down to one
   line each, relying on the ABC's docstring (left untouched — it's the one canonical copy,
   not a repetition) for the shared contract. Deliberately *kept* format-specific facts that
   aren't part of the generic contract and would otherwise be lost — e.g. that
   `JsonVersionHandler.variable` is a plain top-level key while `Toml`/`Yaml` accept a
   dot-separated path, or that `DockerfileVersionHandler` requires a `directive` kwarg.
   Side effect caught by a real `mkdocs build --strict` run (not just `pytest`): rendering
   the ABC's abstract methods via mkdocstrings surfaced a `griffe` warning that `**kwargs`
   had no type annotation ("No type or annotation for parameter '**kwargs'") — fixed by
   annotating all 23 occurrences across the file as `**kwargs: Any`, verified by diffing
   the strict-build warning count before/after (6 → 4, with the remaining 4 confirmed
   pre-existing and unrelated per item 1 above).

---

## 4. Testing

Coverage is already excellent (99% line coverage, 302 passing tests), so these are
targeted gaps rather than a broad call for "more tests." Line coverage is now 100%
across every file in `src/bumpcalver` as of this pass.

1. ✅ **DONE (2026-07-25) — No regression test for YAML key ordering or TOML/XML comment
   preservation.** Added alongside the fixes in Refactoring §2.1–2.3:
   `test_yaml_handler_update_version_preserves_key_order`,
   `test_toml_handler_update_version_preserves_comments`, and
   `test_xml_handler_update_version_preserves_declaration_and_comments` in
   `tests/test_handlers.py`, all using real temporary files (no mocking of the underlying
   `yaml`/`tomlkit`/`ElementTree` calls) so they actually exercise the real formatting/library
   behavior instead of assuming it away.

2. ✅ **DONE (2026-07-25) — the last uncovered lines, both resolved.** The `cli.py:187,
   190-191` exception path no longer exists as described — it was extracted into
   `_read_current_version()`/`_cached_current_version()` during the Refactoring §2.4
   decomposition, which is now directly unit-tested (`test_read_current_version_handler_exception_returns_none`
   in `tests/test_cli_helpers.py`) and at 100% coverage as a byproduct, not a deliberate
   testing-pass fix. The `utils.py` `_parse_hybrid_version` except branch **is** a real,
   deliberate fix: added `TestParseHybridVersionNoBuildCount` in
   `tests/test_hybrid_versioning.py`, using a hybrid format with no `{build_count}`
   placeholder at all (so the compiled regex has no `build_count` named group and
   `m.group("build_count")` raises `IndexError`) — a realistic case, not a contrived one:
   a project that bumps major/minor/patch by hand and only wants a date suffix.

3. ✅ **DONE (2026-07-25) — No type-checking gate in CI.** Added `[tool.mypy]` to
   `pyproject.toml` (`warn_return_any`, `warn_unused_configs`, `warn_redundant_casts`,
   `no_implicit_optional`, scoped to `src/bumpcalver` only — not `tests/`, which leans on
   dynamically-typed `mock`/`monkeypatch` patterns that don't pay for themselves under
   mypy), a `type-check` job in `.github/workflows/testing.yml` (runs once, not across the
   full OS/Python matrix, since it's a static check against a single pinned target
   version), a `mirrors-mypy` pre-commit hook (verified for real — installed the hook
   environment and ran it, not just added the YAML), and a `make mypy`/`make validate`
   target. A permissive first pass surfaced exactly **one** real bug in the whole
   codebase — `not_found_message: str = None` in `handlers.py`, an implicit-Optional
   PEP 484 violation — fixed to `Optional[str] = None`. Installing precise stub packages
   (`types-PyYAML`, `types-toml`) instead of reaching for a blanket
   `ignore_missing_imports = True` surfaced 3 more real gaps under `warn_return_any`; fixed
   2 (an untyped `operation_func` callback parameter in `_handle_read_operation`, and
   `_HANDLER_REGISTRY: Dict[str, type]` widened to the accurate `Dict[str, Type[VersionHandler]]`)
   and scoped-suppressed the third (`json.load`'s return type is unavoidably `Any` — a
   stdlib-boundary limitation, not a bug — with a `# type: ignore[no-any-return]` and a
   comment explaining why). Zero mypy errors in the final state.

4. ✅ **Already resolved — no separate Windows-specific test needed.** The Makefile
   encoding fix from Refactoring §2.7 already shipped with
   `test_makefile_handler_read_version_uses_explicit_utf8_encoding`, which asserts the
   `open()` call arguments directly (`encoding="utf-8"` is actually passed). That's a
   *stronger* test than the Windows-content test originally proposed here: it fails on
   any platform the instant the code regresses, rather than only failing when actually
   executed on a Windows runner with a non-UTF-8 locale.

5. ✅ **DONE (2026-07-25) — Property-based tests for the version-parsing regex machinery,
   which found a real bug.** Added `tests/test_version_parsing_properties.py` with three
   `hypothesis` properties (dot-separated CalVer, hybrid semver+calendar, and the
   bare-CLI-defaults dash-separated case), each round-tripping `format → parse_version`
   across hundreds of randomized date/count/semver combinations against a fixed, known-
   supported `version_format`/`date_format` pair (deliberately *not* randomizing the format
   strings themselves — some format combinations are inherently ambiguous by construction,
   which isn't a bug to find). Writing these surfaced a genuine, previously-undiscovered
   bug: `parse_version` never round-tripped bumpcalver's **own built-in zero-config CLI
   defaults** (`version_format="{current_date}-{build_count:03}"` + `date_format="%Y.%m.%d"`)
   — `_parse_dynamic_version` had no branch for "current_date + build_count with a non-dot
   separator," so it silently fell through to `None`, and a second same-day bump with no
   config file at all would reset the build count to `001` forever instead of incrementing.
   Verified the real-world impact via `get_build_version` (not just `parse_version` in
   isolation) before fixing, fixed it with a narrowly-scoped addition to
   `_parse_dynamic_version` that reuses the already-more-robust `_parse_hybrid_version`
   regex builder, and confirmed the property test actually catches the regression by
   reverting the fix, watching it fail (shrunk to `2000.01.01-000`), then restoring it.
   Also documented the pattern in `docs/development-guide.md`'s new "Property-Based Tests"
   subsection, with a verified-by-running-it excerpt from the real test file.

---

## 5. Capability Expansion Opportunities

**Status (2026-07-25): items 1, 2, 3, 4, and 6 fully done — code, tests, and docs. Item 5
deliberately deferred with rationale (see its entry).**

1. ✅ **DONE — No "generic"/plain-text version handler.**
   Added two new handlers to `handlers.py` (registered as `"text"` and `"regex"` in
   `_HANDLER_REGISTRY`):
   - `TextVersionHandler` — whole-file-is-the-version, no key at all (e.g. a bare `VERSION`
     file). `variable` is ignored.
   - `RegexVersionHandler` — generic handler driven by a user-supplied `pattern` kwarg (regex
     with exactly one capture group). Covers Ruby/Rust/Go/etc. with no dedicated handler.
     `update_version_in_files()` and `cli.py`'s `_read_current_version()` were both updated to
     thread a new `"pattern"` config key through to handlers (mirroring how `"directive"`
     already works for Dockerfile).
   - **Two real bugs were found and fixed while building this** (both via actually running
     the feature end-to-end, not just unit tests):
     1. The first `update_version` implementation caught `re.error` around the
        capture-group lookup, but `match.span(1)` on a pattern with zero capture groups
        actually raises `IndexError`, not `re.error` — it crashed uncaught. Fixed by
        validating `compiled.groups == 1` once in a shared `_compile_pattern()` helper (used
        by both `read_version` and `update_version`) instead of catching the wrong exception
        type after the fact.
     2. Running the real Ruby recipe from `docs/examples/configuration.md` with `--build`
        printed `No 'pattern' provided` and reset the build count to `.1` on *every* run —
        `get_build_version()` in `utils.py` has its own separate read path from `cli.py`'s
        `_read_current_version()`, and only the latter had been updated to thread `pattern`
        through. Fixed by adding the same `pattern`/`directive` kwarg-building to
        `get_build_version()`. This is exactly the class of bug the Testing pass's
        hypothesis-based property tests found earlier in the session (a real code path never
        exercised by the existing unit tests, only found by running the actual feature) —
        the unit tests for `RegexVersionHandler` and `update_version_in_files()` never
        exercised `get_build_version()`'s independent read path at all.
   - Tests: `tests/test_handlers.py` (18 new tests for the handlers themselves — real
     tmp_path files, a real Ruby-shaped example matching `examples/version.rb`'s actual
     content, a real Rust `const` example, explicit coverage of every error path including
     bug 1 above) and `tests/test_utils.py` (2 new tests for bug 2 above: a mocked test
     mirroring the existing `directive`-threading test, and a real end-to-end test bumping a
     real regex-handled file twice on the same day and asserting the build count actually
     increments — confirmed both fail against the pre-fix code and pass after, same as every
     other regression test this session).
   - Verified end-to-end via real CLI invocations (not just unit tests) with both handlers
     configured together in one `bumpcalver.toml`, and separately via the exact recipe now
     published in the docs.
   - **Docs**: README.md/`docs/index.md` (file_type list + new "Generic File Types"
     subsection + two new `[[tool.bumpcalver.file]]` example blocks), `docs/modules.md`
     (`:::` entries for both new classes), and `docs/examples/configuration.md` (the
     pre-existing "Ruby Gem" recipe was updated — not just supplemented — since it
     previously recommended pointing the `python` handler at Ruby files as a documented
     workaround; that's now called out explicitly as coincidental rather than real support,
     with `regex` recommended instead; plus a new "Bare VERSION File" recipe for `text`).
     Every example config block added or changed was verified by actually running it through
     the real CLI, not just visually checked.

2. ✅ **DONE (2026-07-25) — No plugin/entry-point mechanism for custom handlers.**
   Third-party packages can now register a `VersionHandler` for a new `file_type` without
   forking `bumpcalver`, via a `"bumpcalver.handlers"` entry-point group declared in their own
   `pyproject.toml`:
   ```toml
   [project.entry-points."bumpcalver.handlers"]
   myformat = "my_package.handlers:MyFormatHandler"
   ```
   Implementation in `handlers.py`:
   - `_iter_plugin_entry_points()` isolates the one Python-version-dependent API difference in
     `importlib.metadata.entry_points()`: it returns an `EntryPoints` collection with `.select()`
     on 3.10+, but a plain `dict` keyed by group name on 3.9 (the package's `requires-python`
     floor, even though CI's matrix only actually exercises 3.10-3.14). Both branches are
     unit-tested directly by mocking `entry_points()` itself.
   - `_discover_plugin_handlers()` (wrapped in `functools.lru_cache` — scanning installed
     package metadata isn't free and a single CLI run may look up several file types; cleared
     via `.cache_clear()` in tests) does the actual discovery, and encodes three deliberate
     trust-boundary decisions, each covered by both a unit test and a manual smoke test before
     the automated tests were written:
     1. **Built-in file_types always win.** A plugin claiming an existing name (e.g. `"toml"`)
        is ignored with a stderr warning — installing an unrelated package can never silently
        change how your existing files are handled.
     2. **A broken plugin degrades gracefully, not fatally.** An entry point that fails to
        `.load()`, or loads something that isn't a `VersionHandler` subclass, is skipped with a
        stderr warning; `get_version_handler()` raises the same `ValueError` it would for a
        genuinely-unknown type rather than crashing the whole command.
     3. **Duplicate plugin names**: first one found wins, with a stderr warning naming both.
   - `get_version_handler()` now checks `_HANDLER_REGISTRY` first and only consults
     `_discover_plugin_handlers()` on a miss — meaning entry-point scanning is skipped entirely
     for the common case of looking up a built-in type. One consequence worth knowing: this
     means the "built-in wins" collision warning only actually prints when discovery is
     triggered by *something* (an unknown-type lookup or `available_file_types()`), not on
     every lookup of the colliding built-in name — a lookup that never needs plugin data never
     scans for it.
   - New `available_file_types()` function returns every usable `file_type`, built-in and
     plugin combined — useful for introspection/self-tests in a plugin's own package.
   - Tests: 11 new tests in `tests/test_handlers.py`, all using `unittest.mock` to simulate
     `EntryPoint` objects via `monkeypatch.setattr("src.bumpcalver.handlers._iter_plugin_entry_points", ...)`
     — successful discovery and use via `get_version_handler`, built-in-precedence-over-collision
     (via `available_file_types()`, per the short-circuit behavior above), load-failure
     graceful skip, non-`VersionHandler`-subclass rejection, duplicate-name first-wins,
     unknown-type-with-no-plugins still raises, `available_file_types()` correctness with and
     without plugins installed, `lru_cache` actually caches (call-counting fake), and both
     branches of `_iter_plugin_entry_points()`'s Python-version bridge.
   - **Verified end-to-end with a real installable package**, not just mocks: built
     `examples/bumpcalver-plugin-example/` — a real, separate Python package (its own
     `pyproject.toml` with `[project.entry-points."bumpcalver.handlers"]`, an `IniVersionHandler`
     reusing the base class's `_read_key_value_file`/`_update_key_value_file` helpers) that
     registers an `"ini"` file_type that does not exist anywhere in `bumpcalver`'s own source.
     `pip install -e` both packages into an isolated scratch venv, then ran the real
     `bumpcalver --build` CLI against `examples/bumpcalver-plugin-example/example.ini`
     (`file_type = "ini"` declared in that package's own `[tool.bumpcalver]` config) and
     confirmed the file was actually rewritten (`VERSION=1.0.0` → a real calver build version)
     — this is what caught that `bumpcalver`'s config auto-discovery prefers `pyproject.toml`
     over `bumpcalver.toml` when both exist in a directory, which meant the plugin package's own
     `pyproject.toml` (needed for the entry point) was shadowing a separate `bumpcalver.toml` I'd
     initially written; fixed by moving the `[tool.bumpcalver]` section into the same
     `pyproject.toml` instead of using two files. Verification artifacts (`.bumpcalver/`,
     `bumpcalver-history.json`, `__pycache__/`) were cleaned up afterward and `example.ini` reset
     to its checked-in starting value; not wired into the automated `pytest` suite (installing
     packages during unit test runs would side-effect the shared test environment), matching how
     other slow/risky-for-CI verification was handled elsewhere this session.
   - **Docs**: new "Distributing Your Handler as a Plugin" section in `docs/development-guide.md`
     (right after the existing "File Format Support" section it builds on); "Custom File Types
     via Plugins" subsection added to both README.md and `docs/index.md` (near-duplicate content
     — see §3.3 below for the still-open dedup item covering both files); `docs/modules.md` gets
     a new `:::` entry for `available_file_types()` and an updated intro paragraph linking to the
     new dev-guide section.
   - `mkdocs build --strict` confirmed to still produce only the same 4 known pre-existing
     warnings (print-site plugin ordering, two broken links unrelated to this change) — no new
     warnings from the added docs pages/links.

3. ✅ **DONE — No `--dry-run` flag.** Added `--dry-run` to
   `cli.py`. Extracted `_files_that_would_change()` (shared by both the no-op guard and the
   dry-run preview — `_all_files_already_updated()` is now a thin wrapper over it). When
   `--dry-run` is set, prints the version and file list that *would* change (or a no-op
   message) and returns before any backup/write/git-tag code runs. Explicitly rejected in
   combination with `--undo`/`--undo-id`/`--list-history` (raises `UsageError`) — without
   that guard the flag would be silently ignored on that path, which would be a real footgun.
   Tests in `tests/test_cli.py`: a mocked-style test asserting `update_version_in_files`/
   `create_git_tag` are never called, and — the stronger proof — a real end-to-end test using
   `runner.isolated_filesystem()` with actual files, asserting file content is byte-for-byte
   unchanged and no `.bumpcalver/`/`bumpcalver-history.json` artifacts get created. 100%
   coverage on `cli.py` maintained throughout. Documented in README.md's "Version Bump
   Options" list and in the generated `docs/cli-reference.md`.

4. ✅ **DONE — No way to point at a config file outside the
   CWD.** `load_config()` now accepts an optional `config_path` parameter; `cli.py` adds
   `--config-file` (`envvar="BUMPCALVER_CONFIG"`, `click.Path(exists=True, dir_okay=False)`).
   Two design decisions worth knowing about if you pick this back up:
   - **File paths inside the config now resolve relative to the config file's own directory**,
     not the CLI's cwd — that's the actual point of the feature (monorepo/wrapper-script use
     case). `project_root` in `main()` is computed from `os.path.dirname(os.path.abspath(config_file))`
     when `--config-file` is given, `os.getcwd()` otherwise.
   - **Backups/undo history follow project_root too now**, not just `os.getcwd()` —
     `BackupManager(backup_dir=..., history_file=...)` is now constructed with explicit paths
     under `project_root` in `cli.py`'s `main()` (it already supported this via constructor
     args; it just wasn't being passed before). Without this, `--config-file` pointing
     elsewhere would split-brain: files updated in the target project, but undo history
     recorded wherever the CLI happened to be invoked from — meaning `--undo` run later from
     the actual project directory would never find it.
   - `--config-file` is explicitly rejected in combination with undo options for the same
     reason as `--dry-run` above (undo doesn't know about `project_root` at all yet).
   - **This required fixing 8 existing test mocks** in `tests/test_cli.py` and 1 in
     `test_cli_helpers.py`/others that replaced `load_config`/`BackupManager` with zero-arg
     lambdas (`lambda: mock_config`) — these broke because the real functions now always
     receive an argument (even if `None`). Fixed by widening to `lambda *args, **kwargs: ...`.
     If you see this failure pattern again after further changes, this is the fix.
   - New tests in `test_config.py` (4: explicit path not found, arbitrary non-"pyproject.toml"
     filename treated as flat-style, an explicit path *named* `pyproject.toml` elsewhere still
     treated as nested, explicit path bypasses cwd auto-discovery even when a real
     `pyproject.toml` exists in cwd) and `test_cli.py` (4: real cross-directory end-to-end test
     asserting the target project's file changes and backups land next to it not in the
     invoking cwd, env var variant, click's own nonexistent-path rejection, conflict-with-undo
     guard). 100% coverage maintained. Documented in README.md's "Version Bump Options" list
     and in the generated `docs/cli-reference.md`.

5. **NOT STARTED — No machine-readable output mode.** A `--json` flag emitting the computed
   version/updated files/operation ID as structured JSON. Deliberately deferred — it requires
   restructuring the scattered `print()` calls throughout `main()` (need to either suppress
   them or route them to stderr under `--json`), which is more invasive than the other items
   here for comparatively speculative value (no forcing function like a discovered bug pushed
   this one, unlike most other items this session).

6. ✅ **DONE — Undo/backup storage gitignore guidance.** Investigated rather than assumed:
   `docs/undo.md` **already has** a complete, correct "Recommended .gitignore Entries"
   section — my original claim that no such guidance existed was wrong (same kind of
   mis-assessment as the Documentation pass's item 4; correcting the record here rather than
   re-writing docs that already existed). What actually needed fixing: **this repo's own
   `bumpcalver-history.json` was tracked in git despite `.gitignore` already listing it** —
   the file was committed before that `.gitignore` rule was added, and git doesn't
   retroactively untrack files just because a rule appears later. Fixed with
   `git rm --cached bumpcalver-history.json` (file left on disk, just untracked going
   forward) — **this is staged but not yet committed**. `.bumpcalver/` itself had no tracked
   files, so nothing else needed the same treatment.

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

**Known-limitations disclosure** (playbook §10.8, "don't overclaim"): Refactoring §2.1–2.3
above are now fixed (2026-07-25) — YAML key ordering, TOML comments, and the XML declaration
all survive an `update_version` call — so the instructions no longer need to warn about those
as blanket risks. One narrower, permanent caveat remains and should still be disclosed: XML
comments that appear in the *prolog* (before the root element's opening tag) are still
dropped, since that's a structural `ElementTree` limitation rather than a bug (see the
`XmlVersionHandler` class docstring). This is exactly playbook lesson §10.7 in action — the
instructions must be kept in sync with the code as it evolves, not written once and forgotten.

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

1. ✅ Fix YAML key-reordering and TOML/XML comment/declaration loss (§2.1–2.3) — these were
   silent data-loss bugs, not just style issues. **Done 2026-07-25.**
2. ✅ Add the regression tests that would have caught them (§4.1). **Done 2026-07-25.**
3. ✅ Regenerate/fix `docs/modules.md` (§3.1) — it used to misrepresent the public API,
   including omitting the undo and hybrid-versioning features entirely; now generated live
   from source via `mkdocstrings` so it can't drift again. **Done 2026-07-25**, alongside
   the rest of the Documentation Improvements pass (§3.1, §3.2, §3.5 done; §3.3 deferred
   with rationale; §3.4 was already covered, corrected and enriched instead — see their
   entries above).
4. ✅ Add `mypy` to CI (§4.3) — **done 2026-07-25**, alongside the rest of the Testing pass
   (§4.1, §4.2, §4.3, §4.5 done; §4.4 confirmed already covered — see their entries above).
   The Makefile encoding gap (§2.7) — **done 2026-07-25**, alongside the rest of the
   Refactoring Opportunities pass (§2.1–2.8; §2.9 tooling-consolidation intentionally
   deferred, see its entry above).
5. ✅ Capability Expansion pass (§5) — `text`/`regex` generic handlers, `--dry-run`,
   `--config-file`/`BUMPCALVER_CONFIG`, the `bumpcalver-history.json` gitignore-tracking fix,
   and the plugin/entry-point mechanism (§5 item 2, including a real installable example
   package, tests, and docs) are all done — the last of these **done 2026-07-25**. Only a
   `--json` output mode (§5 item 5) remains deliberately deferred — see its entry above for
   why. Everything else in this document beyond §5 and the still-open items called out inline
   (§2.9 tooling consolidation, §3.3 timezones.md dedup, §4.4 n/a) is genuinely additive and
   can be prioritized against actual user requests.
