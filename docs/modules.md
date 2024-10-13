
# Functions

## `get_current_date()`

Returns the current date in the specified timezone.

**Signature:**

```python
def get_current_date(timezone: str = default_timezone) -> str:
```

**Parameters:**

- `timezone` (str): The timezone to use for date calculations. Defaults to `"America/New_York"`.

**Returns:**

- `str`: The current date in the format `"YYYY-MM-DD"`.

**Raises:**

- `ZoneInfoNotFoundError`: If the specified timezone is invalid.

**Example:**

```python
current_date = get_current_date(timezone="UTC")
```

---

## `get_current_datetime_version()`

Returns the current date and time in the specified timezone.

**Signature:**

```python
def get_current_datetime_version(timezone: str = default_timezone) -> str:
```

**Parameters:**

- `timezone` (str): The timezone to use for date and time calculations.

**Returns:**

- `str`: The current date and time in the format `"YYYY-MM-DD-HHMM"`.

**Raises:**

- `ZoneInfoNotFoundError`: If the specified timezone is invalid.

**Example:**

```python
current_datetime_version = get_current_datetime_version(timezone="UTC")
```

---

## `get_build_version()`

Generates a build version based on the current date and build count.

**Signature:**

```python
def get_build_version(file_config: dict, version_format: str, timezone: str = default_timezone) -> str:
```

**Parameters:**

- `file_config` (dict): Configuration for the file containing the version string.
  - `path` (str): File path.
  - `variable` (str, optional): The variable name holding the version.
  - `pattern` (str, optional): A regex pattern to locate the version string.
- `version_format` (str): Format string for the version, including placeholders `{current_date}` and `{build_count}`.
- `timezone` (str): Timezone for date calculations.

**Returns:**

- `str`: The generated build version.

**Raises:**

- `ValueError`: If the version format is invalid.
- `KeyError`: If required keys are missing in `file_config`.

**Example:**

```python
file_config = {"path": "version.py", "variable": "__version__"}
version = get_build_version(file_config, "{current_date}-{build_count:03}", timezone="UTC")
```

---

## `update_version_in_files()`

Updates the version string in the specified files.

**Signature:**

```python
def update_version_in_files(new_version: str, file_configs: list[dict]) -> list[str]:
```

**Parameters:**

- `new_version` (str): The new version string to set.
- `file_configs` (list of dict): List of file configurations.

**Returns:**

- `list[str]`: List of files that were updated.

**Raises:**

- `FileNotFoundError`: If a specified file is not found.
- `Exception`: If an error occurs while updating a file.

**Example:**

```python
file_configs = [
    {"path": "version.py", "variable": "__version__"},
    {"path": "setup.cfg", "pattern": r"^version = .*$"},
]
updated_files = update_version_in_files("2023-10-05-001", file_configs)
```

---

## `load_config()`

Loads the configuration from the `pyproject.toml` file.

**Signature:**

```python
def load_config() -> dict:
```

**Returns:**

- `dict`: A dictionary containing configuration settings.

**Raises:**

- `toml.TomlDecodeError`: If there is an error parsing the configuration file.

**Example:**

```python
config = load_config()
```

---

## `create_git_tag()`

Creates a Git tag with the new version.

**Signature:**

```python
def create_git_tag(version: str, files_to_commit: list[str], auto_commit: bool) -> None:
```

**Parameters:**

- `version` (str): The version string to use as the Git tag.
- `files_to_commit` (list of str): Files to commit before tagging.
- `auto_commit` (bool): Whether to automatically commit changes.

**Raises:**

- `subprocess.CalledProcessError`: If an error occurs during Git operations.

**Example:**

```python
create_git_tag("2023-10-05-001", ["version.py"], auto_commit=True)
```

---

## `main()`

CLI entry point for version bumping.

**Signature:**

```python
def main(beta: bool, build: bool, timezone: str, git_tag: bool, auto_commit: bool) -> None:
```

**Parameters:**

- `beta` (bool): Use beta versioning if `True`.
- `build` (bool): Use build count versioning if `True`.
- `timezone` (str): Timezone for date calculations.
- `git_tag` (bool): Create a Git tag with the new version if `True`.
- `auto_commit` (bool): Automatically commit changes when creating a Git tag if `True`.

**Raises:**

- `toml.TomlDecodeError`: If there is an error parsing the configuration file.
- `ValueError`: If there is an error generating the version.
- `KeyError`: If required keys are missing in the configuration.

**Example:**

This function is decorated with `click.command()` and is intended to be run from the command line.



---

## Error Handling

- **Unknown Timezone**: If an invalid timezone is specified, the default timezone (`America/New_York`) is used, and a warning is printed.

- **File Not Found**: If a specified file is not found during version update, an error message is printed.

- **Invalid Build Count**: If the existing build count in a file is invalid, it resets to `1`, and a warning is printed.

- **Git Errors**: Errors during Git operations are caught, and an error message is displayed.

- **Malformed Configuration**: If the `pyproject.toml` file is malformed, an error is printed, and the program exits.

---

## License

*Include license information here if applicable.*

---

## Additional Notes

- **Customization**: The CLI is designed to be flexible. By modifying the `version_format` in the configuration, you can change how versions are generated.

- **File Configuration**: You can specify multiple files in the `file` section of the configuration to update version strings in different places.

- **Version Patterns**: If the `variable` approach doesn't suit your files, you can use regex `pattern` to locate and replace the version string.
