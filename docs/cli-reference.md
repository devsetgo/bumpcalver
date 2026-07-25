# CLI Reference

This is the literal output of `bumpcalver --help`. A test
(`tests/test_docs.py::test_cli_reference_matches_help_output`) asserts this
block stays byte-for-byte in sync with the live `click.Command` — if you add,
remove, or reword a CLI option, that test will fail until this page is
regenerated to match.

```text
Usage: bumpcalver [OPTIONS]

  Bump this project's version and write it to every configured file.

  Reads `[tool.bumpcalver]` from `pyproject.toml` (or `bumpcalver.toml`) for the
  file list and defaults; CLI flags override config values where both exist. At
  most one of `--beta`/`--rc`/`--release`/`--custom` may be set. Optionally
  creates a git tag and/or commit — or preview with `--dry-run` instead of
  writing anything. Undo a previous run with `--undo`, `--undo-id`, or `--list-
  history` (mutually exclusive with every version-bump option, including `--dry-
  run`).

Options:
  -V, --version                   Show the version and exit.
  --beta                          Add -beta to version
  --rc                            Add -rc to version
  --release                       Add -release to version
  --custom TEXT                   Add -<WhatEverYouWant> to version
  --build                         Use build count versioning
  --timezone TEXT                 Timezone for date calculations (default: value
                                  from config or America/New_York)
  --git-tag / --no-git-tag        Create a Git tag with the new version
  --auto-commit / --no-auto-commit
                                  Automatically commit changes when creating a
                                  Git tag
  --undo                          Undo the last version bump operation
  --undo-id TEXT                  Undo a specific operation by ID
  --list-history                  List recent operations that can be undone
  --bump [major|minor|patch]      Increment the specified semantic version
                                  component in config
  --dry-run                       Show what would change without writing any
                                  files or creating a git tag/commit
  --config-file FILE              Path to a pyproject.toml/bumpcalver.toml to
                                  use instead of auto-discovery in the current
                                  directory (env var: BUMPCALVER_CONFIG). File
                                  paths inside it are resolved relative to the
                                  config file's own directory, not the current
                                  directory.
  --help                          Show this message and exit.
```

## Notes

- `--beta`, `--rc`, `--release`, and `--custom` are mutually exclusive — only
  one pre-release suffix option may be set per invocation.
- `--undo`, `--undo-id`, and `--list-history` are mutually exclusive with
  every version-bump option (`--beta`/`--rc`/`--release`/`--custom`/`--build`/
  `--bump`/`--dry-run`/`--config-file`); combining them raises a usage error
  before any version logic runs.
- `--git-tag`/`--auto-commit` and their `--no-` counterparts override the
  `git_tag`/`auto_commit` config values for a single invocation.
- `--dry-run` computes and prints the version/files that would change without
  writing anything or touching git.
- `--config-file` (or `BUMPCALVER_CONFIG`) points at a config outside the
  current directory. File paths inside that config — and the undo
  backups/history for the resulting operation — resolve relative to the
  config file's own directory, not wherever `bumpcalver` was invoked from.
- See the [Configuration](index.md#configuration-options) section for the
  corresponding `pyproject.toml`/`bumpcalver.toml` settings (`version_format`,
  `beta_format`, `rc_format`, `release_format`, `major`/`minor`/`patch`, etc.).
