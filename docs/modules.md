# API Reference

This page is generated directly from the library's docstrings via
[mkdocstrings](https://mkdocstrings.github.io/), so it always reflects the
installed version's actual signatures and behavior rather than a
hand-maintained copy that can drift out of sync with the code.

For the command-line options, see [CLI Reference](cli-reference.md) instead —
that page is generated from the CLI's live `--help` output.

## CLI Entry Point

::: bumpcalver.cli.main
    options:
      show_source: false

## Versioning Utilities

::: bumpcalver.utils.get_current_date
    options:
      show_source: false

::: bumpcalver.utils.get_current_datetime_version
    options:
      show_source: false

::: bumpcalver.utils.get_build_version
    options:
      show_source: false

::: bumpcalver.utils.parse_version
    options:
      show_source: false

::: bumpcalver.utils.apply_prerelease_suffix
    options:
      show_source: false

::: bumpcalver.utils.update_semantic_in_config
    options:
      show_source: false

::: bumpcalver.utils.parse_dot_path
    options:
      show_source: false

## Configuration

::: bumpcalver.config.load_config
    options:
      show_source: false

## Git Integration

::: bumpcalver.git_utils.create_git_tag
    options:
      show_source: false

## File Handlers

Every supported `file_type` (see [Configuration](index.md#configuration-options))
is backed by a `VersionHandler` subclass. All of them share the same
`read_version`/`update_version` contract defined on the abstract base class —
see the [handler extension guide](development-guide.md#file-format-support)
if you're adding support for a new file format, or
[distributing your handler as a plugin](development-guide.md#distributing-your-handler-as-a-plugin)
if you'd rather ship it as a separate installable package via the
`bumpcalver.handlers` entry-point group.

::: bumpcalver.handlers.VersionHandler

::: bumpcalver.handlers.get_version_handler
    options:
      show_source: false

::: bumpcalver.handlers.available_file_types
    options:
      show_source: false

::: bumpcalver.handlers.update_version_in_files
    options:
      show_source: false

### Format-specific handlers

::: bumpcalver.handlers.PythonVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.TomlVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.YamlVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.JsonVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.XmlVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.DockerfileVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.MakefileVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.PropertiesVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.EnvVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.SetupCfgVersionHandler
    options:
      show_source: false

### Generic handlers

For formats with no dedicated handler above.

::: bumpcalver.handlers.TextVersionHandler
    options:
      show_source: false

::: bumpcalver.handlers.RegexVersionHandler
    options:
      show_source: false

## AI Assistant Instructions

See [AI Assistant Instructions](ai-instructions.md) for the full narrative
guide (what's covered, what isn't, the security contract). API reference:

::: bumpcalver.ai_instructions.get_app_instructions
    options:
      show_source: false

::: bumpcalver.ai_instructions.available_instruction_profiles
    options:
      show_source: false

::: bumpcalver.ai_instructions.suggested_instruction_filename
    options:
      show_source: false

## Undo / Backup

::: bumpcalver.backup_utils.BackupManager
    options:
      show_source: false

::: bumpcalver.undo_utils.undo_last_operation
    options:
      show_source: false

::: bumpcalver.undo_utils.undo_operation_by_id
    options:
      show_source: false

::: bumpcalver.undo_utils.list_undo_history
    options:
      show_source: false
