# Quick Start

### Install

```bash
pip install bumpcalver
```

### Usage

#### Initialize Configuration

Create a `pyproject.toml` file in your project's root directory with the following content:

```toml
[tool.bumpcalver]
version_format = "{current_date}-{build_count:03}"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "version.py"
variable = "__version__"

[[tool.bumpcalver.file]]
path = "src/module_name/__init__.py"
variable = "__version__"
```

This configuration tells **BumpCalver** how to format your version strings, which timezone to use, and which files to update.

#### Basic Version Bump

To bump the version using the current date and build count:

```bash
bumpcalver --build
```

This command will:

- Increment the build count for the current date.
- Update the `__version__` variable in `version.py`.
- Use the timezone specified in your configuration (`UTC` in this case).

#### Beta Versioning

To create a beta version:

```bash
bumpcalver --build --beta
```

This will prefix your version with `beta-`, resulting in a version like `beta-2023-10-05-001`.

#### Specify Timezone

To use a specific timezone (overriding the configuration):

```bash
bumpcalver --build --timezone Europe/London
```

#### Create a Git Tag with Auto-Commit

To bump the version, commit changes, and create a Git tag:

```bash
bumpcalver --build --git-tag --auto-commit
```

This command will:

- Update the version as before.
- Commit the changes to Git.
- Create a Git tag with the new version.

#### Additional Options

- **Disable Git Tagging**:

  ```bash
  bumpcalver --build --no-git-tag
  ```

- **Disable Auto-Commit**:

  ```bash
  bumpcalver --build --no-auto-commit
  ```

---

### See Documentation

For more examples and advanced usage, please refer to the [full documentation](#) or visit the project's repository.

*Note: Replace `#` with the actual link to your documentation or repository.*

---

### Example `version.py` File

Ensure that your `version.py` file (or the file specified in your configuration) contains the version variable:

```python
__version__ = "0.1.0"
```

After running `bumpcalver --build`, it will be updated to:

```python
__version__ = "2023-10-05-001"
```

---

### Integrate with Your Project

You can import the version into your application as needed:

```python
from version import __version__

print(f"Current version: {__version__}")
```

---

### Summary

With **BumpCalver**, you can automate version management based on the calendar date and build counts, ensuring consistent and meaningful version numbers across your project.

---

*For any issues or contributions, please visit the [project repository](#) or contact [support](mailto:support@example.com).*

*Note: Replace placeholders with actual URLs or email addresses relevant to your project.*
