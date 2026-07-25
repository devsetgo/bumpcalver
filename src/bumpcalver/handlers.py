"""
Version handlers for BumpCalver.

Provides read/update handlers for Python, TOML, YAML, JSON, XML, Dockerfile,
Makefile, Properties, .env, and setup.cfg files. Use `get_version_handler(file_type)`
to obtain the right handler, or `update_version_in_files` for batch updates.
"""

import configparser
import json
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type

import tomlkit
from ruamel.yaml import YAML

# Shared, reusable round-trip YAML instance (the ruamel.yaml-recommended
# pattern — cheap to reuse, no per-call setup cost). Round-trip ("rt") is the
# default `typ`; preserve_quotes keeps the source's choice of quoted vs.
# unquoted scalars intact too.
_yaml = YAML()
_yaml.preserve_quotes = True


# Abstract base class for version handlers
class VersionHandler(ABC):
    """Abstract base class for version handlers.

    Subclasses implement `read_version`/`update_version` for one file format;
    see the [handler extension guide](development-guide.md#file-format-support)
    for the shared helpers (`_read_key_value_file`, `_update_key_value_file`,
    `_handle_regex_update`, etc.) available for reuse.
    """

    @abstractmethod
    def read_version(
        self, file_path: str, variable: str, **kwargs: Any
    ) -> Optional[str]:  # pragma: no cover
        """Reads the version string from the specified file.

        Args:
            file_path (str): The path to the file.
            variable (str): The variable name that holds the version string.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: The version string if found, otherwise None.
        """

    @abstractmethod
    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:  # pragma: no cover
        """Updates the version string in the specified file.

        Args:
            file_path (str): The path to the file.
            variable (str): The variable name that holds the version string.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the version was successfully updated, otherwise False.
        """

    def format_version(self, version: str, standard: str) -> str:
        """Formats the version string according to the specified standard.

        Args:
            version (str): The version string to format.
            standard (str): The versioning standard to use (e.g., "python" for PEP 440).

        Returns:
            str: The formatted version string.
        """
        if standard == "python":
            return self.format_pep440_version(version)
        return version

    def format_pep440_version(self, version: str) -> str:
        """Formats the version string according to PEP 440.

        This method replaces hyphens and underscores with dots and ensures no leading
        zeros in numeric segments.

        Args:
            version (str): The version string to format.

        Returns:
            str: The formatted version string.
        """
        # Replace hyphens and underscores with dots
        version = version.replace("-", ".").replace("_", ".")
        # Ensure no leading zeros in numeric segments
        version = re.sub(r"\b0+(\d)", r"\1", version)
        return version

    def _read_file_safe(self, file_path: str, encoding: str = "utf-8") -> Optional[str]:
        """Safely read file content with error handling.

        Args:
            file_path (str): Path to the file to read.
            encoding (str): File encoding, defaults to utf-8.

        Returns:
            Optional[str]: File content if successful, None if error.
        """
        try:
            with open(file_path, "r", encoding=encoding) as file:
                return file.read()
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

    def _write_file_safe(self, file_path: str, content: str, encoding: str = "utf-8") -> bool:
        """Safely write file content with error handling.

        Args:
            file_path (str): Path to the file to write.
            content (str): Content to write.
            encoding (str): File encoding, defaults to utf-8.

        Returns:
            bool: True if successful, False if error.
        """
        try:
            with open(file_path, "w", encoding=encoding) as file:
                file.write(content)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False

    def _format_version_with_standard(self, new_version: str, **kwargs: Any) -> str:
        """Apply version formatting based on version_standard kwarg.

        Args:
            new_version (str): The version to format.
            **kwargs: Keyword arguments containing version_standard.

        Returns:
            str: Formatted version string.
        """
        version_standard = kwargs.get("version_standard", "default")
        return self.format_version(new_version, version_standard)

    def _find_key_value_in_lines(self, lines: List[str], variable: str) -> Optional[int]:
        """Find the line index containing a key=value pair.

        Args:
            lines (List[str]): List of file lines.
            variable (str): Variable name to search for.

        Returns:
            Optional[int]: Line index if found, None otherwise.
        """
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                key, _ = stripped_line.split("=", 1)
                if key.strip() == variable:
                    return i
        return None

    def _log_variable_not_found(self, variable: str, file_path: str, prefix: str = "") -> None:
        """Log a standardized 'variable not found' message.

        Args:
            variable (str): The variable name that was not found.
            file_path (str): The file path being searched.
            prefix (str): Optional prefix for the variable description.
        """
        prefix_text = f"{prefix} " if prefix else ""
        print(f"{prefix_text}Variable '{variable}' not found in {file_path}")

    def _log_success_update(self, file_path: str, extra_info: str = "") -> None:
        """Log a standardized success message for file updates.

        Args:
            file_path (str): The file path that was updated.
            extra_info (str): Optional extra information to include.
        """
        if extra_info:
            print(f"Updated {extra_info} in {file_path}")
        else:
            print(f"Updated {file_path}")

    def _handle_regex_update(self, file_path: str, pattern: re.Pattern, replacement_func, new_version: str,
                           variable: str, not_found_message: Optional[str] = None) -> bool:
        """Handle regex-based file updates with standardized error handling.

        Args:
            file_path (str): Path to the file to update.
            pattern (re.Pattern): Compiled regex pattern for matching.
            replacement_func: Function to generate replacement text.
            new_version (str): The new version string.
            variable (str): The variable name being updated.
            not_found_message (str): Custom message when variable not found.

        Returns:
            bool: True if update successful, False otherwise.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False

        new_content, num_subs = pattern.subn(replacement_func, content)

        if num_subs > 0:
            return self._write_file_safe(file_path, new_content)
        else:
            if not_found_message:
                print(not_found_message)
            else:
                self._log_variable_not_found(variable, file_path)
            return False

    def _update_key_value_file(
        self, file_path: str, variable: str, new_version: str, not_found_label: str = "Variable"
    ) -> bool:
        """Shared update logic for key=value line-based files (Properties, .env)."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            line_index = self._find_key_value_in_lines(lines, variable)
            if line_index is None:
                print(f"{not_found_label} '{variable}' not found in {file_path}")
                return False

            key, _ = lines[line_index].strip().split("=", 1)
            lines[line_index] = f"{key}={new_version}\n"
            with open(file_path, "w", encoding="utf-8") as file:
                file.writelines(lines)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False

    def _read_key_value_file(
        self, file_path: str, variable: str, strip_quotes: bool = False
    ) -> Optional[str]:
        """Shared read logic for key=value line-based files (Properties, .env).

        Args:
            file_path (str): Path to the file to read.
            variable (str): The key whose value should be returned.
            strip_quotes (bool): Strip surrounding single/double quotes from the
                value, as .env files conventionally allow (e.g. VERSION="1.0").

        Returns:
            Optional[str]: The value if the key is found, otherwise None.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == variable:
                            value = value.strip()
                            if strip_quotes:
                                value = value.strip("\"'")
                            return value
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return None

    def _handle_read_operation(
        self, file_path: str, operation_func: Callable[[], Optional[str]]
    ) -> Optional[str]:
        """Handle read operations with standardized error handling."""
        try:
            return operation_func()
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None


class PythonVersionHandler(VersionHandler):
    """Handler for `variable = "..."`-style assignments in Python files, e.g. `__version__`."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads `variable`'s value from a `variable = "..."` (or `'...'`) assignment."""
        version_pattern = re.compile(
            rf'^\s*{re.escape(variable)}\s*=\s*["\'](.+?)["\']\s*$', re.MULTILINE
        )

        def read_operation():
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            match = version_pattern.search(content)
            if match:
                return match.group(1)
            self._log_variable_not_found(variable, file_path)  # no pragma: no cover
            return None # no pragma: no cover

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates `variable`'s assignment in place, preserving its quote style and surrounding whitespace."""
        new_version = self._format_version_with_standard(new_version, **kwargs)
        version_pattern = re.compile(
            rf'^(\s*{re.escape(variable)}\s*=\s*)(["\'])(.+?)(["\'])(\s*)$',
            re.MULTILINE,
        )

        def replacement(match):
            return f"{match.group(1)}{match.group(2)}{new_version}{match.group(4)}{match.group(5)}"

        return self._handle_regex_update(file_path, version_pattern, replacement, new_version, variable)


class TomlVersionHandler(VersionHandler):
    """Handler for TOML files (e.g. `pyproject.toml`), using `tomlkit`.

    Uses `tomlkit` rather than the plain `toml` package so comments and
    formatting elsewhere in the file survive an update — `toml.load`/`toml.dump`
    round-trip through a plain dict and silently drop every comment, which
    matters since this handler's primary target commonly carries them.
    """

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the value at `variable`, a dot-separated key path (e.g. `"tool.project.version"`)."""
        def read_operation():
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = tomlkit.load(file)
            keys = variable.split(".")
            temp = toml_content
            for key in keys:
                temp = temp.get(key)
                if temp is None:
                    self._log_variable_not_found(variable, file_path)
                    return None
            return str(temp)

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates the value at `variable` (a dot-separated key path) in place."""
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = tomlkit.load(file)

            keys = variable.split(".")
            temp = toml_content
            for key in keys[:-1]:
                if key not in temp:
                    temp[key] = {} # no pragma: no cover
                temp = temp[key]
            last_key = keys[-1]
            if last_key in temp:
                # Assigning into an existing key (rather than replacing the
                # table) is what makes tomlkit preserve that key's inline
                # comment/formatting instead of rewriting the whole line.
                temp[last_key] = new_version
            else:
                print(f"Variable '{variable}' not found in {file_path}")
                return False

            with open(file_path, "w", encoding="utf-8") as file:
                tomlkit.dump(toml_content, file)

            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class YamlVersionHandler(VersionHandler):
    """Handler for YAML files, using `ruamel.yaml`'s round-trip mode.

    Uses `ruamel.yaml` rather than the plain `PyYAML` package so comments,
    key order, and quote style elsewhere in the file survive an update —
    `yaml.safe_load`/`yaml.safe_dump` round-trip through plain dicts and
    silently drop every comment (and, unless `sort_keys=False` is passed,
    alphabetize every key too). Mirrors why `TomlVersionHandler` uses
    `tomlkit` instead of the plain `toml` package.
    """

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the value at `variable`, a dot-separated key path (e.g. `"configuration.version"`)."""
        def read_operation():
            with open(file_path, "r", encoding="utf-8") as f:
                data = _yaml.load(f)
            keys = variable.split(".")
            temp = data
            for key in keys:
                temp = temp.get(key)
                if temp is None:
                    self._log_variable_not_found(variable, file_path)
                    return None
            return str(temp)

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates the value at `variable` (a dot-separated key path) in place."""
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = _yaml.load(f)
            keys = variable.split(".")
            temp = data
            for key in keys[:-1]:
                temp = temp.setdefault(key, {}) # no pragma: no cover
            temp[keys[-1]] = new_version
            with open(file_path, "w", encoding="utf-8") as f:
                _yaml.dump(data, f)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class JsonVersionHandler(VersionHandler):
    """Handler for JSON files (e.g. `package.json`); `variable` is a top-level key only."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the top-level key `variable` (unlike Toml/Yaml, this is a plain key, not a dot-separated path)."""
        def read_operation():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(variable)

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates the top-level key `variable` in place."""
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data[variable] = new_version
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class XmlVersionHandler(VersionHandler):
    """Handler for XML files, using `xml.etree.ElementTree`.

    `update_version` preserves the `<?xml ?>` declaration and any comments nested
    *inside* the root element. Comments in the prolog (before the root element's
    opening tag) are not preserved — an `ElementTree` limitation (`Element`/
    `TreeBuilder` model the tree from the root element down, so anything outside
    it is dropped on write regardless of parser options); `lxml` would be needed
    for full prolog fidelity.
    """

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the text of the element at `variable`, an ElementTree `find()` path (e.g. `"version"` or `"metadata/version"`)."""
        def read_operation():
            tree = ET.parse(file_path)
            root = tree.getroot()
            element = root.find(variable)
            if element is not None:
                return element.text
            self._log_variable_not_found(variable, file_path)
            return None

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates the text of the element at `variable` in place (see class docstring for formatting fidelity)."""
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            # insert_comments=True keeps comments nested inside the root element
            # in the parsed tree (see class docstring for what this does and
            # doesn't cover); xml_declaration=True on write restores the
            # <?xml ?> prolog, which ET.write() otherwise drops by default.
            parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
            tree = ET.parse(file_path, parser=parser)
            root = tree.getroot()
            element = root.find(variable)
            if element is not None:
                element.text = new_version
                tree.write(file_path, xml_declaration=True, encoding="UTF-8")
                print(f"Updated {file_path}")
                return True
            print(f"Variable '{variable}' not found in {file_path}")
            return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class DockerfileVersionHandler(VersionHandler):
    """Handler for `ARG`/`ENV` directives in Dockerfiles; requires a `directive` kwarg."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads `variable`'s value from an `ARG`/`ENV` line; requires `directive="ARG"` or `"ENV"` in kwargs."""
        directive = kwargs.get("directive", "").upper()
        if directive not in ["ARG", "ENV"]:
            print(
                f"Invalid or missing directive for variable '{variable}' in {file_path}."
            )
            return None

        pattern = re.compile(
            rf"^\s*{directive}\s+{re.escape(variable)}\s*=\s*(.+?)\s*$", re.MULTILINE
        )

        def read_operation():
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            match = pattern.search(content)
            if match:
                return match.group(1).strip()
            print(f"No {directive} variable '{variable}' found in {file_path}")
            return None

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates `variable`'s `ARG`/`ENV` line in place; requires `directive="ARG"` or `"ENV"` in kwargs."""
        directive = kwargs.get("directive", "").upper()
        if directive not in ["ARG", "ENV"]:
            print(
                f"Invalid or missing directive for variable '{variable}' in {file_path}."
            )
            return False

        new_version = self._format_version_with_standard(new_version, **kwargs)
        pattern = re.compile(
            rf"(^\s*{directive}\s+{re.escape(variable)}\s*=\s*)(.+?)\s*$", re.MULTILINE
        )

        def replacement(match):
            return f"{match.group(1)}{new_version}"

        not_found_message = f"No {directive} variable '{variable}' found in {file_path}"
        success = self._handle_regex_update(file_path, pattern, replacement, new_version, variable, not_found_message)

        if success:
            self._log_success_update(file_path, f"{directive} variable '{variable}'")

        return success


class MakefileVersionHandler(VersionHandler):
    """Handler for `VAR = value` / `VAR := value` lines in Makefiles."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the value from the first line starting with `variable` (e.g. `VERSION = 1.0`)."""
        def read_operation():
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    if line.startswith(variable):
                        return line.split("=")[1].strip()
            self._log_variable_not_found(variable, file_path)  # no pragma: no cover
            return None  # no pragma: no cover

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates `variable`'s value in place (accepts both `VAR = value` and `VAR := value`)."""
        new_version = self._format_version_with_standard(new_version, **kwargs)
        version_pattern = re.compile(
            rf"^({re.escape(variable)}\s*[:]?=\s*)(.*)$", re.MULTILINE
        )

        def replacement(match):
            return f"{match.group(1)}{new_version}"

        return self._handle_regex_update(file_path, version_pattern, replacement, new_version, variable)


class PropertiesVersionHandler(VersionHandler):
    """Handler for `key=value` properties files (e.g. `sonar-project.properties`)."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the value of the `variable` key from a `key=value` line."""
        return self._read_key_value_file(file_path, variable)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        new_version = self._format_version_with_standard(new_version, **kwargs)
        return self._update_key_value_file(file_path, variable, new_version, "Property")


class EnvVersionHandler(VersionHandler):
    """Handler for `KEY=VALUE` `.env` files; strips surrounding quotes on read."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the value of the `variable` key from a `KEY=value` line, stripping surrounding quotes if present."""
        return self._read_key_value_file(file_path, variable, strip_quotes=True)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        new_version = self._format_version_with_standard(new_version, **kwargs)
        return self._update_key_value_file(file_path, variable, new_version, "Environment variable")


class SetupCfgVersionHandler(VersionHandler):
    """Handler for `setup.cfg`'s INI-style sections and `key=value` pairs."""

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads `variable`'s value: `"section.key"` reads that section directly, a bare key searches all sections."""
        try:
            config = configparser.ConfigParser()
            config.read(file_path)

            # Handle dot notation like "metadata.version"
            if "." in variable:
                section, key = variable.split(".", 1)
                if section in config and key in config[section]:
                    return config[section][key].strip()
            else:
                # Search in all sections for the key
                for section in config.sections():
                    if variable in config[section]:
                        return config[section][variable].strip()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return None

    def _update_dot_notation_variable(self, config, variable: str, new_version: str) -> bool:
        """Update variable using dot notation (e.g., "metadata.version").

        Args:
            config: ConfigParser instance
            variable (str): Variable in dot notation format
            new_version (str): New version to set

        Returns:
            bool: True if updated successfully
        """
        section, key = variable.split(".", 1)
        if section not in config:
            config.add_section(section)
        config[section][key] = new_version
        return True

    def _update_simple_variable(self, config, variable: str, new_version: str) -> bool:
        """Update variable by searching all sections.

        Args:
            config: ConfigParser instance
            variable (str): Variable name to search for
            new_version (str): New version to set

        Returns:
            bool: True if variable was found and updated, False if variable was created in metadata section
        """
        # Search in all sections for the key and update the first match
        for section in config.sections():
            if variable in config[section]:
                config[section][variable] = new_version
                return True

        # If not found in any section, add to metadata section
        if 'metadata' not in config:
            config.add_section('metadata')
        config['metadata'][variable] = new_version
        return False  # Variable was not found, so we created it

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Updates `variable`'s value in place; a bare key not found in any section is created under `[metadata]`."""
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            config = configparser.ConfigParser()
            config.read(file_path)

            # Update the variable based on its format
            if "." in variable:
                self._update_dot_notation_variable(config, variable, new_version)
            else:
                self._update_simple_variable(config, variable, new_version)

            with open(file_path, "w", encoding="utf-8") as file:
                config.write(file)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class TextVersionHandler(VersionHandler):
    """Handler for bare version files whose entire content *is* the version
    (e.g. a `VERSION` file containing just `1.2.3`, as used by many
    shell-based release pipelines). `variable` is ignored — there is no key,
    the whole file is the value.
    """

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the entire file, stripped of surrounding whitespace, as the version."""
        content = self._read_file_safe(file_path)
        return content.strip() if content is not None else None

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Overwrites the entire file with `new_version` plus a trailing newline."""
        new_version = self._format_version_with_standard(new_version, **kwargs)
        return self._write_file_safe(file_path, f"{new_version}\n")


class RegexVersionHandler(VersionHandler):
    """Generic handler for formats with no dedicated handler (Ruby `VERSION = "..."`,
    Rust `const VERSION: &str = "...";`, Go `var Version = "..."`, etc.).

    Driven entirely by a `pattern` kwarg: a regex string with exactly one capture
    group around the version. Set `file_type = "regex"` and pass `pattern` in the
    file's config, e.g. `pattern = 'VERSION = "(.+?)"'` for a Ruby file. `variable`
    is not used for matching — it only appears in log messages — since the pattern
    itself locates the version.
    """

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        """Reads the text captured by `pattern`'s first group."""
        pattern = self._compile_pattern(kwargs.get("pattern", ""), file_path)
        if pattern is None:
            return None

        def read_operation():
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            match = pattern.search(content)
            if match:
                return match.group(1)
            self._log_variable_not_found(variable or "pattern", file_path)
            return None

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        """Replaces the text captured by `pattern`'s first group with `new_version`, leaving everything else on the line untouched."""
        new_version = self._format_version_with_standard(new_version, **kwargs)
        pattern = self._compile_pattern(kwargs.get("pattern", ""), file_path)
        if pattern is None:
            return False

        def replacement(match: re.Match) -> str:
            full_start = match.start(0)
            group_start, group_end = match.span(1)
            full = match.group(0)
            return f"{full[: group_start - full_start]}{new_version}{full[group_end - full_start :]}"

        return self._handle_regex_update(file_path, pattern, replacement, new_version, variable or "pattern")

    def _compile_pattern(self, pattern_str: str, file_path: str) -> Optional[re.Pattern]:
        """Compile the user-supplied pattern, reporting a clear error if it's missing/invalid.

        Validates the capture-group count here (rather than catching the
        IndexError that match.span(1) would raise later) so both read_version
        and update_version get the same clear error message from one place.
        """
        if not pattern_str:
            print(f"No 'pattern' provided for regex handler on {file_path}.")
            return None
        try:
            compiled = re.compile(pattern_str, re.MULTILINE)
        except re.error as e:
            print(f"Invalid regex pattern for {file_path}: {e}")
            return None
        if compiled.groups != 1:
            print(
                f"Pattern for {file_path} must contain exactly one capture group "
                f"(found {compiled.groups})."
            )
            return None
        return compiled


_HANDLER_REGISTRY: Dict[str, Type[VersionHandler]] = {
    "python": PythonVersionHandler,
    "toml": TomlVersionHandler,
    "yaml": YamlVersionHandler,
    "json": JsonVersionHandler,
    "xml": XmlVersionHandler,
    "dockerfile": DockerfileVersionHandler,
    "makefile": MakefileVersionHandler,
    "properties": PropertiesVersionHandler,
    "env": EnvVersionHandler,
    "setup.cfg": SetupCfgVersionHandler,
    "text": TextVersionHandler,
    "regex": RegexVersionHandler,
}


def get_version_handler(file_type: str) -> VersionHandler:
    """Return a handler instance for the given file type.

    Raises ValueError for unsupported types.
    """
    handler_class = _HANDLER_REGISTRY.get(file_type)
    if handler_class is None:
        raise ValueError(f"Unsupported file type: {file_type}")
    return handler_class()


def update_version_in_files(
    new_version: str, file_configs: List[Dict[str, Any]]
) -> List[str]:
    """Updates the version string in multiple files based on the provided configurations.

    This function iterates over the provided file configurations, updates the version
    string in each file using the appropriate version handler, and returns a list of
    files that were successfully updated.

    Args:
        new_version (str): The new version string to set in the files.
        file_configs (List[Dict[str, Any]]): A list of dictionaries containing file configuration details.
            Each dictionary should have the following keys:
                - "path" (str): The path to the file.
                - "file_type" (str): The type of the file (e.g., "python", "toml", "yaml", "json", "xml",
                  "dockerfile", "makefile", "properties", "env", "setup.cfg", "text", "regex").
                - "variable" (str, optional): The variable name that holds the version string.
                - "directive" (str, optional): The directive for Dockerfile (e.g., "ARG" or "ENV").
                - "pattern" (str, optional): Regex with one capture group, required for file_type="regex".
                - "version_standard" (str, optional): The versioning standard to follow (default is "default").

    Returns:
        List[str]: A list of file paths that were successfully updated.

    Example:
        file_configs = [
            {"path": "version.py", "file_type": "python", "variable": "__version__"},
            {"path": "pyproject.toml", "file_type": "toml", "variable": "tool.bumpcalver.version"},
        ]
        updated_files = update_version_in_files("2023.10.05", file_configs)
    """
    files_updated: List[str] = []

    for file_config in file_configs:
        file_path: str = file_config["path"]
        file_type: str = file_config.get("file_type", "")
        variable: str = file_config.get("variable", "")
        directive: str = file_config.get("directive", "")
        pattern: str = file_config.get("pattern", "")
        version_standard: str = file_config.get("version_standard", "default")

        handler = get_version_handler(file_type)
        if handler.update_version(
            file_path,
            variable,
            new_version,
            directive=directive,
            pattern=pattern,
            version_standard=version_standard,
        ):
            files_updated.append(file_path)

    return files_updated
