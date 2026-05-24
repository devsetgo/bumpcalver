"""
Version handlers for BumpCalver.

Provides read/update handlers for Python, TOML, YAML, JSON, XML, Dockerfile,
Makefile, Properties, .env, and setup.cfg files. Use `get_version_handler(file_type)`
to obtain the right handler, or `update_version_in_files` for batch updates.
"""

import json
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import toml
import yaml


# Abstract base class for version handlers
class VersionHandler(ABC):
    """Abstract base class for version handlers.

    This class provides the interface for reading and updating version strings
    in various file formats. Subclasses must implement the `read_version` and
    `update_version` methods.

    Methods:
        read_version: Reads the version string from the specified file.
        update_version: Updates the version string in the specified file.
        format_version: Formats the version string according to the specified standard.
        format_pep440_version: Formats the version string according to PEP 440.
    """

    @abstractmethod
    def read_version(
        self, file_path: str, variable: str, **kwargs
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
        self, file_path: str, variable: str, new_version: str, **kwargs
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

    def _format_version_with_standard(self, new_version: str, **kwargs) -> str:
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
                           variable: str, not_found_message: str = None) -> bool:
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

    def _handle_read_operation(self, file_path: str, operation_func) -> Optional[str]:
        """Handle read operations with standardized error handling."""
        try:
            return operation_func()
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None


class PythonVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in Python files.

    This class provides methods to read and update version strings in Python files.
    It uses regular expressions to locate and modify the version string.

    Methods:
        read_version: Reads the version string from the specified Python file.
        update_version: Updates the version string in the specified Python file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified Python file.

        This method searches for the version string in the specified Python file
        using a regular expression that matches the variable name.

        Args:
            file_path (str): The path to the Python file.
            variable (str): The variable name that holds the version string.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: The version string if found, otherwise None.

        Raises:
            Exception: If there is an error reading the file.
        """
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
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified Python file.

        This method searches for the version string in the specified Python file
        using a regular expression that matches the variable name and updates it
        with the new version string.

        Args:
            file_path (str): The path to the Python file.
            variable (str): The variable name that holds the version string.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the version was successfully updated, otherwise False.

        Raises:
            Exception: If there is an error reading or writing the file.
        """
        new_version = self._format_version_with_standard(new_version, **kwargs)
        version_pattern = re.compile(
            rf'^(\s*{re.escape(variable)}\s*=\s*)(["\'])(.+?)(["\'])(\s*)$',
            re.MULTILINE,
        )

        def replacement(match):
            return f"{match.group(1)}{match.group(2)}{new_version}{match.group(4)}{match.group(5)}"

        return self._handle_regex_update(file_path, version_pattern, replacement, new_version, variable)


class TomlVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in TOML files.

    This class provides methods to read and update version strings in TOML files.
    It uses the `toml` library to parse and modify the version string.

    Methods:
        read_version: Reads the version string from the specified TOML file.
        update_version: Updates the version string in the specified TOML file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified TOML file.

        This method searches for the version string in the specified TOML file
        using the provided variable name, which can be a dot-separated path.

        Args:
            file_path (str): The path to the TOML file.
            variable (str): The variable name that holds the version string, which can be a dot-separated path.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: The version string if found, otherwise None.

        Raises:
            Exception: If there is an error reading the file.
        """
        def read_operation():
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = toml.load(file)
            keys = variable.split(".")
            temp = toml_content
            for key in keys:
                temp = temp.get(key)
                if temp is None:
                    self._log_variable_not_found(variable, file_path)
                    return None
            return temp

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified TOML file.

        This method searches for the version string in the specified TOML file
        using the provided variable name, which can be a dot-separated path, and updates it
        with the new version string.

        Args:
            file_path (str): The path to the TOML file.
            variable (str): The variable name that holds the version string, which can be a dot-separated path.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the version was successfully updated, otherwise False.

        Raises:
            Exception: If there is an error reading or writing the file.
        """
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = toml.load(file)

            keys = variable.split(".")
            temp = toml_content
            for key in keys[:-1]:
                if key not in temp:
                    temp[key] = {} # no pragma: no cover
                temp = temp[key]
            last_key = keys[-1]
            if last_key in temp:
                temp[last_key] = new_version
            else:
                print(f"Variable '{variable}' not found in {file_path}")
                return False

            with open(file_path, "w", encoding="utf-8") as file:
                toml.dump(toml_content, file)

            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class YamlVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in YAML files.

    This class provides methods to read and update version strings in YAML files.
    It uses the `yaml` library to parse and modify the version string.

    Methods:
        read_version: Reads the version string from the specified YAML file.
        update_version: Updates the version string in the specified YAML file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified YAML file.

        This method searches for the version string in the specified YAML file
        using the provided variable name, which can be a dot-separated path.

        Args:
            file_path (str): The path to the YAML file.
            variable (str): The variable name that holds the version string, which can be a dot-separated path.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: The version string if found, otherwise None.

        Raises:
            Exception: If there is an error reading the file.
        """
        def read_operation():
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            keys = variable.split(".")
            temp = data
            for key in keys:
                temp = temp.get(key)
                if temp is None:
                    self._log_variable_not_found(variable, file_path)
                    return None
            return temp

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified YAML file.

        This method searches for the version string in the specified YAML file
        using the provided variable name, which can be a dot-separated path, and updates it
        with the new version string.

        Args:
            file_path (str): The path to the YAML file.
            variable (str): The variable name that holds the version string, which can be a dot-separated path.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the version was successfully updated, otherwise False.

        Raises:
            Exception: If there is an error reading or writing the file.
        """
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            keys = variable.split(".")
            temp = data
            for key in keys[:-1]:
                temp = temp.setdefault(key, {}) # no pragma: no cover
            temp[keys[-1]] = new_version
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class JsonVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in JSON files.

    This class provides methods to read and update version strings in JSON files.
    It uses the `json` library to parse and modify the version string.

    Methods:
        read_version: Reads the version string from the specified JSON file.
        update_version: Updates the version string in the specified JSON file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified JSON file.

        This method searches for the version string in the specified JSON file
        using the provided variable name.

        Args:
            file_path (str): The path to the JSON file.
            variable (str): The variable name that holds the version string.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: The version string if found, otherwise None.

        Raises:
            Exception: If there is an error reading the file.
        """
        def read_operation():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(variable)

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified JSON file.

        This method searches for the version string in the specified JSON file
        using the provided variable name and updates it with the new version string.

        Args:
            file_path (str): The path to the JSON file.
            variable (str): The variable name that holds the version string.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the version was successfully updated, otherwise False.

        Raises:
            Exception: If there is an error reading or writing the file.
        """
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
    """Handler for reading and updating version strings in XML files.

    This class provides methods to read and update version strings in XML files.
    It uses the `xml.etree.ElementTree` library to parse and modify the version string.

    Methods:
        read_version: Reads the version string from the specified XML file.
        update_version: Updates the version string in the specified XML file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified XML file.

        This method searches for the version string in the specified XML file
        using the provided variable name.

        Args:
            file_path (str): The path to the XML file.
            variable (str): The variable name that holds the version string.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: The version string if found, otherwise None.

        Raises:
            Exception: If there is an error reading the file.
        """
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
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified XML file.

        This method searches for the version string in the specified XML file
        using the provided variable name and updates it with the new version string.

        Args:
            file_path (str): The path to the XML file.
            variable (str): The variable name that holds the version string.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the version was successfully updated, otherwise False.

        Raises:
            Exception: If there is an error reading or writing the file.
        """
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            element = root.find(variable)
            if element is not None:
                element.text = new_version
                tree.write(file_path)
                print(f"Updated {file_path}")
                return True
            print(f"Variable '{variable}' not found in {file_path}")
            return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


class DockerfileVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in Dockerfile files.

    This class provides methods to read and update version strings in Dockerfile files.
    It uses regular expressions to locate and modify the version string in ARG or ENV directives.

    Methods:
        read_version: Reads the version string from the specified Dockerfile.
        update_version: Updates the version string in the specified Dockerfile.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified Dockerfile.

        This method searches for the version string in the specified Dockerfile
        using the provided variable name and directive (ARG or ENV).

        Args:
            file_path (str): The path to the Dockerfile.
            variable (str): The variable name that holds the version string.
            **kwargs: Additional keyword arguments, including 'directive' which should be 'ARG' or 'ENV'.

        Returns:
            Optional[str]: The version string if found, otherwise None.

        Raises:
            Exception: If there is an error reading the file.
        """
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
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified Dockerfile.

        This method searches for the version string in the specified Dockerfile
        using the provided variable name and directive (ARG or ENV), and updates it
        with the new version string.

        Args:
            file_path (str): The path to the Dockerfile.
            variable (str): The variable name that holds the version string.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments, including 'directive' which should be 'ARG' or 'ENV'.

        Returns:
            bool: True if the version was successfully updated, otherwise False.

        Raises:
            Exception: If there is an error reading or writing the file.
        """
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
    """Handler for reading and updating version strings in Makefile files.

    This class provides methods to read and update version strings in Makefile files.
    It uses regular expressions to locate and modify the version string.

    Methods:
        read_version: Reads the version string from the specified Makefile.
        update_version: Updates the version string in the specified Makefile.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified Makefile.

        This method searches for the version string in the specified Makefile
        using the provided variable name.

        Args:
            file_path (str): The path to the Makefile.
            variable (str): The variable name that holds the version string.
            **kwargs: Additional keyword arguments.

        Returns:
            Optional[str]: The version string if found, otherwise None.

        Raises:
            Exception: If there is an error reading the file.
        """
        def read_operation():
            with open(file_path, "r") as file:
                for line in file:
                    if line.startswith(variable):
                        return line.split("=")[1].strip()
            self._log_variable_not_found(variable, file_path)  # no pragma: no cover
            return None  # no pragma: no cover

        return self._handle_read_operation(file_path, read_operation)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified Makefile.

        This method searches for the version string in the specified Makefile
        using the provided variable name and updates it with the new version string.

        Args:
            file_path (str): The path to the Makefile.
            variable (str): The variable name that holds the version string.
            new_version (str): The new version string.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the version was successfully updated, otherwise False.

        Raises:
            Exception: If there is an error reading or writing the file.
        """
        new_version = self._format_version_with_standard(new_version, **kwargs)
        version_pattern = re.compile(
            rf"^({re.escape(variable)}\s*[:]?=\s*)(.*)$", re.MULTILINE
        )

        def replacement(match):
            return f"{match.group(1)}{new_version}"

        return self._handle_regex_update(file_path, version_pattern, replacement, new_version, variable)


class PropertiesVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in Properties files.

    This class provides methods to read and update version strings in properties files
    such as sonar-project.properties. It handles key=value format where keys and values
    are separated by equals signs.

    Methods:
        read_version: Reads the version string from the specified properties file.
        update_version: Updates the version string in the specified properties file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified properties file.

        Args:
            file_path (str): The path to the properties file.
            variable (str): The property key that holds the version string.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            Optional[str]: The version string if found, otherwise None.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == variable:
                            return value.strip()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return None

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        new_version = self._format_version_with_standard(new_version, **kwargs)
        return self._update_key_value_file(file_path, variable, new_version, "Property")


class EnvVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in .env files.

    This class provides methods to read and update version strings in .env files.
    It handles KEY=VALUE format where keys and values are separated by equals signs.

    Methods:
        read_version: Reads the version string from the specified .env file.
        update_version: Updates the version string in the specified .env file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified .env file.

        Args:
            file_path (str): The path to the .env file.
            variable (str): The environment variable name that holds the version string.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            Optional[str]: The version string if found, otherwise None.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == variable:
                            # Remove quotes if present
                            value = value.strip().strip("\"'")
                            return value
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return None

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        new_version = self._format_version_with_standard(new_version, **kwargs)
        return self._update_key_value_file(file_path, variable, new_version, "Environment variable")


class SetupCfgVersionHandler(VersionHandler):
    """Handler for reading and updating version strings in setup.cfg files.

    This class provides methods to read and update version strings in setup.cfg files.
    It handles INI format with sections and key=value pairs.

    Methods:
        read_version: Reads the version string from the specified setup.cfg file.
        update_version: Updates the version string in the specified setup.cfg file.
    """

    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
        """Reads the version string from the specified setup.cfg file.

        Args:
            file_path (str): The path to the setup.cfg file.
            variable (str): The variable name that holds the version string (e.g., "metadata.version").
            **kwargs: Additional keyword arguments (unused).

        Returns:
            Optional[str]: The version string if found, otherwise None.
        """
        try:
            import configparser
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
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:
        """Updates the version string in the specified setup.cfg file.

        Args:
            file_path (str): The path to the setup.cfg file.
            variable (str): The variable name that holds the version string (e.g., "metadata.version").
            new_version (str): The new version string to set.
            **kwargs: Additional keyword arguments including version_standard.

        Returns:
            bool: True if the version was successfully updated, False otherwise.
        """
        new_version = self._format_version_with_standard(new_version, **kwargs)

        try:
            import configparser
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


_HANDLER_REGISTRY: Dict[str, type] = {
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
                - "file_type" (str): The type of the file (e.g., "python", "toml", "yaml", "json", "xml", "dockerfile", "makefile").
                - "variable" (str, optional): The variable name that holds the version string.
                - "directive" (str, optional): The directive for Dockerfile (e.g., "ARG" or "ENV").
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
        version_standard: str = file_config.get("version_standard", "default")

        handler = get_version_handler(file_type)
        if handler.update_version(
            file_path,
            variable,
            new_version,
            directive=directive,
            version_standard=version_standard,
        ):
            files_updated.append(file_path)

    return files_updated
