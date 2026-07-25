# Contributing to BumpCalver

Thank you for your interest in contributing to BumpCalver! This guide will help you get started with contributing to the project, whether you're fixing bugs, adding features, improving documentation, or writing tests.

## Ways to Contribute

- **🐛 Report Bugs**: Found something broken? Let us know!
- **✨ Add Features**: Implement new functionality or file format support
- **📚 Improve Documentation**: Help make our docs clearer and more comprehensive
- **🧪 Add Tests**: Increase test coverage and reliability
- **🔧 Fix Issues**: Pick up existing issues and solve problems
- **💡 Suggest Improvements**: Share ideas for making BumpCalver better

## Getting Started

### 1. Fork and Clone the Repository

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/bumpcalver.git
cd bumpcalver

# Add the original repository as upstream
git remote add upstream https://github.com/devsetgo/bumpcalver.git
```

### 2. Set Up Your Development Environment

#### Prerequisites

- Python 3.9 or higher
- Git
- Make (optional, for using the Makefile)

#### Create a Virtual Environment

```bash
# Create and activate a virtual environment
python -m venv _venv
source _venv/bin/activate  # On Windows: _venv\Scripts\activate

# Or if you prefer using the existing one
source _venv/bin/activate
```

#### Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt

# Or use the Makefile
make install
```

#### Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks for code quality
make pre-commit

# Or manually:
pre-commit install
```

### 3. Development Workflow

#### Create a Feature Branch

```bash
# Create a new branch for your feature/fix
git checkout -b feature/your-feature-name

# Or for bug fixes:
git checkout -b fix/issue-description
```

#### Make Your Changes

Follow the project structure:

```
bumpcalver/
├── src/bumpcalver/          # Main package code
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration handling
│   ├── handlers.py         # File format handlers
│   ├── utils.py            # Utility functions
│   ├── git_utils.py        # Git operations
│   ├── undo_utils.py       # Undo functionality
│   └── backup_utils.py     # Backup management
├── tests/                   # Test suite
│   ├── test_*.py           # Test modules
│   └── test_files/         # Test data
├── docs/                    # Documentation
└── examples/               # Example configurations
```

### 4. Code Quality Standards

#### Code Formatting

We use several tools to maintain code quality:

```bash
# Format code (runs all formatters)
make format

# Individual tools:
make isort      # Sort imports
make black      # Code formatting
make autoflake  # Remove unused imports
make ruff       # Lint and fix
make mypy       # Type-check src/bumpcalver

# Validate without changes (includes mypy)
make validate
```

#### Type Checking

`src/bumpcalver` is type-checked with `mypy` (config in `pyproject.toml`'s
`[tool.mypy]`), both as a pre-commit hook and as a standalone `type-check`
job in CI (`.github/workflows/testing.yml`) — it only needs to run once,
not across the full OS/Python test matrix, since it checks against a single
pinned `python_version`. Only `src/bumpcalver` is checked, not `tests/`;
test code leans on `unittest.mock`/`monkeypatch` patterns that are
dynamically typed by nature, so checking it doesn't pay for itself the way
checking the library's public surface does.

#### Code Style Guidelines

- **Follow PEP 8**: Python code should follow PEP 8 style guidelines
- **Type Hints**: Use type hints for function parameters and return values
- **Docstrings**: Document functions and classes with clear docstrings
- **Comments**: Explain complex logic with inline comments

Example:

```python
def parse_version(
    version: str,
    version_format: Optional[str] = None,
    date_format: Optional[str] = None
) -> Optional[tuple]:
    """Parse a version string and return date and count components.

    This function can parse version strings in various formats based on
    the provided format specifications.

    Args:
        version: The version string to parse
        version_format: Format template for the version
        date_format: Date format specification

    Returns:
        Tuple of (date_string, build_count) or None if parsing fails

    Example:
        >>> parse_version("24.Q4.001", "{current_date}.{build_count:03}", "%y.Q%q")
        ('24.Q4', 1)
    """
    # Implementation here...
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test files
python -m pytest tests/test_utils.py -v

# Run tests with coverage
make test-coverage

# Quick tests (no pre-commit hooks)
make quick-test
```

### Writing Tests

#### Test Structure

```python
# tests/test_your_feature.py
import pytest
from src.bumpcalver.your_module import your_function


class TestYourFeature:
    """Test suite for your feature."""

    def test_basic_functionality(self):
        """Test the basic happy path."""
        result = your_function("input")
        assert result == "expected_output"

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        with pytest.raises(ValueError):
            your_function("invalid_input")

    @pytest.mark.parametrize("input_val,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
        ("input3", "output3"),
    ])
    def test_multiple_cases(self, input_val, expected):
        """Test multiple scenarios with parametrized tests."""
        result = your_function(input_val)
        assert result == expected
```

#### Calendar Versioning Tests

When adding new date format support, add comprehensive tests:

```python
# Add to tests/test_calver_comprehensive.py
def test_your_new_format(self):
    """Test your new calendar versioning format."""
    test_cases = [
        ("version_string", "version_format", "date_format", "expected_date", expected_count),
        # Add multiple test cases
    ]

    for version, version_format, date_format, expected_date, expected_count in test_cases:
        result = parse_version(version, version_format, date_format)
        assert result is not None, f"Failed to parse {version}"
        date_part, build_count = result
        assert date_part == expected_date
        assert build_count == expected_count
```

#### Property-Based Tests

Hand-picked example cases (as above) are good at pinning down specific
known formats, but the format-string-to-regex translation in `utils.py`
(`parse_version`/`_parse_hybrid_version`/`_clean_version_suffixes`) is
general enough that bugs tend to hide in combinations nobody thought to
write an example for — that's exactly how the bug fixed alongside
`tests/test_version_parsing_properties.py` was found (the CLI's own
built-in zero-config defaults never actually round-tripped). For this kind
of "any valid input matching this shape should behave correctly" logic,
prefer a [Hypothesis](https://hypothesis.readthedocs.io/) property test
over enumerating more examples by hand:

```python
# tests/test_version_parsing_properties.py
from datetime import date

from hypothesis import given, settings
from hypothesis import strategies as st

from src.bumpcalver.utils import parse_version

_REASONABLE_DATES = st.dates(min_value=date(2000, 1, 1), max_value=date(2099, 12, 31))
_BUILD_COUNTS = st.integers(min_value=0, max_value=9999)


@given(the_date=_REASONABLE_DATES, build_count=_BUILD_COUNTS)
@settings(max_examples=200)
def test_dot_separated_calver_round_trips(the_date, build_count):
    version_format = "{current_date}.{build_count:03}"
    date_format = "%Y.%m.%d"
    date_str = the_date.strftime(date_format)
    version_string = version_format.format(current_date=date_str, build_count=build_count)

    assert parse_version(version_string, version_format, date_format) == (date_str, build_count)
```

Scope the strategy to a **fixed, known-supported `version_format`/
`date_format` pair** and randomize the *values* plugged into it (dates,
counts, semver components) — don't also randomize the format strings
themselves. Some format combinations are inherently ambiguous to parse
(that's a property of the format, not a bug), so randomizing format
strings produces spurious failures unrelated to real parsing bugs. If
Hypothesis finds a failure, it shrinks to the smallest failing example and
that's usually enough to see the bug immediately; the `.hypothesis/`
example database it creates locally is gitignored.

### Test Data and Isolation

Use the test utilities for isolated testing:

```python
from tests.test_utils_isolated import isolated_test_environment, create_test_file

def test_with_temp_files():
    """Test using temporary files."""
    with isolated_test_environment() as temp_dir:
        test_file = create_test_file(
            temp_dir,
            "test_file.py",
            '__version__ = "1.0.0"\n'
        )

        # Your test logic here
        # Files are automatically cleaned up
```

## Adding New Features

### File Format Support

Every supported `file_type` is backed by a `VersionHandler` subclass in
`src/bumpcalver/handlers.py`. All of them implement the same two-method
contract (`read_version`/`update_version`) defined on the abstract base
class — see the [API Reference](modules.md#file-handlers) for the full,
generated list of existing handlers and the base class's shared helpers.

To add support for a new file format:

1. **Check whether you actually need a new handler.** If your format is
   simple `KEY=value` lines (like `.properties`/`.env`), or the version is
   guarded by a directive keyword on its own line (like Dockerfile's
   `ARG`/`ENV`), the base class already has helpers for exactly that — see
   step 2 before writing a parser from scratch.

2. **Create a Handler**, reusing base-class helpers where they fit your
   format. For a `KEY=value` file, `_read_key_value_file`/
   `_update_key_value_file` do the parsing/writing for you (this is a real,
   tested example — it's exactly how `PropertiesVersionHandler` and
   `EnvVersionHandler` are implemented):

```python
class IniVersionHandler(VersionHandler):
    """Handler for INI-style key=value files, e.g. an app.ini VERSION= line."""

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        return self._read_key_value_file(file_path, variable)

    def update_version(self, file_path: str, variable: str, new_version: str, **kwargs) -> bool:
        new_version = self._format_version_with_standard(new_version, **kwargs)
        return self._update_key_value_file(file_path, variable, new_version, "Setting")
```

   If your format instead needs a regex substitution in place (like Python,
   Makefile, or Dockerfile files), use `_handle_regex_update` the same way
   `PythonVersionHandler.update_version` does. Either way, call
   `self._format_version_with_standard(new_version, **kwargs)` first so your
   handler respects the `version_standard = "python"` config option (PEP 440
   normalization) the same way every other handler does.

3. **Register the Handler** by adding it to `_HANDLER_REGISTRY` in `handlers.py`:

```python
_HANDLER_REGISTRY: Dict[str, type] = {
    # ... existing entries
    "your_format": YourFormatHandler,
}
```

4. **Add Tests** in `tests/test_handlers.py`. Prefer a real temporary file
   over mocking `open`/the underlying parser where practical — that's what
   actually catches formatting-fidelity bugs (see the YAML/TOML/XML handler
   tests for examples: they round-trip a real file and assert comments/key
   order survive, which mocked tests can't verify):

```python
def test_your_format_handler_round_trip(tmp_path):
    handler = YourFormatHandler()
    config_file = tmp_path / "app.your_format"
    config_file.write_text("VERSION=1.0.0\n", encoding="utf-8")

    assert handler.read_version(str(config_file), "VERSION") == "1.0.0"
    assert handler.update_version(str(config_file), "VERSION", "2.0.0") is True
    assert "VERSION=2.0.0" in config_file.read_text(encoding="utf-8")
```

5. **Update Documentation**:
   - Add the new `file_type` value to the list in README.md/`docs/index.md`.
   - Add a `[[tool.bumpcalver.file]]` example to `docs/examples/configuration.md`.
   - No changes needed to `docs/modules.md`/`cli-reference.md` — those are
     generated from the code, so your new handler's docstring (and the
     `_HANDLER_REGISTRY` entry) will show up automatically next time the docs
     are built.

### Distributing Your Handler as a Plugin

Steps 1-2 above (writing the `VersionHandler` subclass) are identical whether
you're contributing it back to `bumpcalver` or shipping it in your own
package. If it's proprietary, niche, or you'd just rather not wait on a PR,
skip step 3 (editing `_HANDLER_REGISTRY`) — register it via the
`bumpcalver.handlers` entry-point group instead, from your own package's
`pyproject.toml`:

```toml
[project.entry-points."bumpcalver.handlers"]
myformat = "my_package.handlers:MyFormatHandler"
```

Once your package is installed in the same environment as `bumpcalver`
(`pip install your-package`), `file_type = "myformat"` becomes usable in
`[[tool.bumpcalver.file]]` entries — no fork, no PR, no changes to
`bumpcalver` itself. `bumpcalver` discovers it via
[`importlib.metadata.entry_points()`](https://docs.python.org/3/library/importlib.metadata.html#entry-points)
the first time a `file_type` lookup misses the built-in registry, and caches
the result for the rest of the process.

A complete, installable example lives in
[`examples/bumpcalver-plugin-example/`](https://github.com/devsetgo/bumpcalver/tree/main/examples/bumpcalver-plugin-example) —
it registers an `ini` file_type that doesn't exist anywhere in `bumpcalver`'s
own source, and its README walks through installing it and running
`bumpcalver --build` against it.

A few things worth knowing about how discovery behaves:

- **Built-in file_types always win.** If your plugin registers a name that
  collides with a built-in (`"toml"`, `"json"`, etc.), `bumpcalver` uses the
  built-in and prints a warning to stderr — a plugin can add new file types,
  not silently override existing ones. Two plugins registering the *same*
  new name is resolved the same way: first one found wins, with a warning.
- **A broken plugin doesn't break your build.** If your entry point fails to
  import, or doesn't point at a `VersionHandler` subclass, `bumpcalver`
  prints a warning and skips it — commands that don't touch your file_type
  still work.
- **`available_file_types()`** (in `bumpcalver.handlers`) returns every
  usable `file_type`, built-in and plugin alike — useful if you want to
  assert your plugin registered correctly, e.g. in your own package's tests.

### Date Format Support

To add new date format patterns:

1. **Update Utils** in `src/bumpcalver/utils.py`:

```python
def get_current_datetime_version(timezone: str, date_format: str) -> str:
    """Add handling for your new date format tokens."""
    # Add custom format handling if needed
```

2. **Add Comprehensive Tests** in `tests/test_calver_comprehensive.py`:

```python
def test_your_date_format(self):
    """Test your new date format pattern."""
    # Add test cases for your format
```

3. **Update Documentation**:
   - Add to calendar versioning guide
   - Include real-world examples

## Documentation

### Writing Documentation

- **Use Clear Examples**: Include practical, working examples
- **Follow Markdown Standards**: Use consistent formatting
- **Test Code Examples**: Ensure all code examples actually work
- **Cross-Reference**: Link to related documentation

### Building Documentation Locally

```bash
# Build and serve documentation locally
make serve-docs

# Build documentation for deployment
make create-docs-local
```

### Documentation Structure

```
docs/
├── index.md                    # Main documentation
├── quickstart.md              # Getting started guide
├── calendar-versioning-guide.md # CalVer patterns (new!)
├── contribute.md              # This file
├── examples/                  # Configuration examples
└── ...
```

## Pull Request Process

### Before Submitting

1. **Ensure Tests Pass**: `make test`
2. **Check Code Quality**: `make format && make validate`
3. **Update Documentation**: If you added features
4. **Add Changelog Entry**: Update relevant sections
5. **Test Locally**: Verify your changes work as expected

### Pull Request Guidelines

1. **Create from Feature Branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Write a Clear Title and Description**:
   ```
   Title: Add support for custom quarterly date formats

   Description:
   - Adds support for custom quarter formats like %y.Q%q
   - Includes comprehensive tests for quarter parsing
   - Updates documentation with examples
   - Fixes issue #93
   ```

3. **Reference Issues**: Link to relevant issues using keywords:
   ```
   Fixes #93
   Closes #45
   Resolves #12
   ```

4. **Add Screenshots/Examples** if relevant

### Review Process

1. **Automated Checks**: CI/CD will run tests automatically
2. **Code Review**: Maintainers will review your code
3. **Address Feedback**: Make requested changes
4. **Merge**: Once approved, your PR will be merged

## Issue Reporting

### Bug Reports

When reporting bugs, include:

```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should have happened

## Actual Behavior
What actually happened

## Environment
- OS:
- Python Version:
- BumpCalver Version:
- Configuration: (paste your pyproject.toml section)

## Additional Context
Any other relevant information
```

### Feature Requests

For feature requests, include:

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Implementation
How might this be implemented?

## Examples
Show what the feature would look like in practice

## Additional Context
Any other relevant information
```

## Development Environment Details

### Makefile Targets

The project includes a comprehensive Makefile:

```bash
# Development workflow
make all                    # Complete workflow: install, format, test, build
make dev-setup             # Set up development environment

# Code quality
make format                # Run all formatters
make validate              # Validate code style
make clean                 # Clean up generated files

# Testing
make test                  # Full test suite
make quick-test           # Fast tests only
make test-coverage        # Tests with coverage report

# Building
make build                # Build the package
make bump                 # Bump version using bumpcalver

# Documentation
make create-docs          # Build and deploy docs
make serve-docs          # Serve docs locally
make list-docs           # List doc versions
```

### Directory Structure

```
bumpcalver/
├── .bumpcalver/          # BumpCalver data
│   └── backups/         # Version backup files
├── _venv/               # Virtual environment
├── docs/                # Documentation source
├── examples/            # Example configurations
├── htmlcov/            # Coverage reports
├── scripts/            # Utility scripts
├── src/                # Source code
│   └── bumpcalver/     # Main package
├── tests/              # Test suite
├── bumpcalver-history.json # Version history
├── makefile            # Build automation
├── pyproject.toml      # Project configuration
└── requirements.txt    # Dependencies
```

### Git Workflow

```bash
# Stay updated with upstream
git fetch upstream
git checkout dev
git merge upstream/dev

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes, commit often
git add .
git commit -m "Add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

## Getting Help

- **GitHub Issues**: [Create an issue](https://github.com/devsetgo/bumpcalver/issues)
- **Discussions**: [GitHub Discussions](https://github.com/devsetgo/bumpcalver/discussions)
- **Documentation**: [Official Docs](https://devsetgo.github.io/bumpcalver/)

## Recognition

Contributors are recognized in:
- **CHANGELOG.md**: All contributions are acknowledged
- **GitHub Contributors**: Automatic recognition
- **Release Notes**: Major contributions are highlighted

Thank you for contributing to BumpCalver! Your efforts help make calendar versioning better for everyone. 🚀
