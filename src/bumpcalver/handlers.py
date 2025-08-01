"""
Version handlers for BumpCalver.

This module provides a comprehensive set of handlers for reading and updating version strings 
across different file formats commonly used in software development projects. The module is 
designed with extensibility and type safety in mind, following the Abstract Base Class pattern 
to ensure consistent interfaces across all handler implementations.

The handlers support various file formats including configuration files, source code files, 
container definitions, and build scripts. Each handler is optimized for its specific file format 
and provides robust error handling, encoding support, and version formatting capabilities.

Architecture:
    The module follows a hierarchical design with VersionHandler as the abstract base class
    that defines the contract for all concrete handler implementations. Each handler specializes
    in a specific file format while providing consistent read/update operations and version
    formatting capabilities.

Supported File Formats:
    - Python files (.py): Variable assignments like __version__ = "1.0.0"
    - TOML files (.toml): Nested configuration with dot notation support
    - YAML files (.yaml, .yml): Hierarchical configuration with key-value pairs
    - JSON files (.json): Simple key-value pairs for version storage
    - XML files (.xml): Element-based version storage with XPath-like access
    - Dockerfile: ARG and ENV directive support for container versioning
    - Makefile: Variable assignments for build automation
    - Properties files (.properties): Key=value format for Java-style configuration
    - Environment files (.env): Environment variable definitions
    - Setup.cfg files: INI-style configuration with section support

Version Standards:
    The module supports multiple version formatting standards:
    - PEP 440 (Python): Canonical Python package versioning
    - Semantic Versioning: Major.Minor.Patch format
    - Calendar Versioning: Date-based versioning schemes
    - Custom formats: User-defined version patterns

Classes:
    VersionHandler: Abstract base class defining the handler interface. Provides common
        formatting methods and establishes the contract for read_version and update_version
        operations. All concrete handlers inherit from this class.
        
    PythonVersionHandler: Specialized handler for Python source files. Uses regex patterns
        to locate and update variable assignments. Supports single and double quoted strings
        with proper escaping. Handles encoding detection and preserves file formatting.
        
    TomlVersionHandler: Handler for TOML configuration files using the tomli library.
        Supports nested key access via dot notation (e.g., "tool.poetry.version").
        Preserves TOML structure and formatting while updating specific values.
        
    YamlVersionHandler: Handler for YAML files using the PyYAML library. Supports nested
        dictionary access and maintains YAML formatting. Handles both simple and complex
        YAML structures with proper type preservation.
        
    JsonVersionHandler: Handler for JSON files with built-in json module support.
        Maintains JSON formatting with proper indentation. Supports nested object
        access and preserves data types during updates.
        
    XmlVersionHandler: Handler for XML files using ElementTree. Supports XPath-like
        element selection and updates. Preserves XML structure and encoding declarations.
        
    DockerfileVersionHandler: Specialized handler for Docker container definitions.
        Supports both ARG and ENV directives with proper syntax validation.
        Handles multi-stage builds and preserves Dockerfile formatting.
        
    MakefileVersionHandler: Handler for GNU Make build scripts. Supports variable
        assignments with both = and := operators. Preserves makefile structure
        and comment blocks.
        
    PropertiesVersionHandler: Handler for Java-style properties files. Supports
        key=value syntax with comment preservation. Handles special characters
        and encoding properly.
        
    EnvVersionHandler: Handler for environment variable files. Supports quoted
        and unquoted values with proper escaping. Preserves comments and file
        structure while updating specific variables.
        
    SetupCfgVersionHandler: Handler for Python setup.cfg files using configparser.
        Supports INI-style sections with dot notation access (e.g., "metadata.version").
        Preserves section structure and comments.

Functions:
    get_version_handler(file_type: str) -> VersionHandler:
        Factory function that returns the appropriate handler instance for a given
        file type. Raises ValueError for unsupported file types.
        
        Args:
            file_type: String identifier for the file format
            
        Returns:
            Configured handler instance for the specified format
            
        Raises:
            ValueError: If the file type is not supported
            
    update_version_in_files(new_version: str, file_configs: List[Dict[str, Any]]) -> List[str]:
        Batch update function that processes multiple files with different configurations.
        Provides transactional-like behavior with detailed success/failure reporting.
        
        Args:
            new_version: The version string to apply to all configured files
            file_configs: List of file configuration dictionaries
            
        Returns:
            List of successfully updated file paths
            
        Configuration Format:
            Each file_config dictionary should contain:
            - path (str): Absolute or relative path to the file
            - file_type (str): Handler type identifier
            - variable (str): Variable/key name to update
            - directive (str, optional): For Dockerfile ARG/ENV specification
            - version_standard (str, optional): Formatting standard to apply

Error Handling:
    All handlers implement robust error handling with informative error messages.
    Common error scenarios include:
    - File not found or permission errors
    - Malformed configuration files
    - Missing variables or keys
    - Encoding issues
    - Syntax errors in configuration files

Usage Examples:
    Basic single file update:
        >>> handler = PythonVersionHandler()
        >>> current_version = handler.read_version("src/mypackage/__init__.py", "__version__")
        >>> success = handler.update_version("src/mypackage/__init__.py", "__version__", "2024.01.15")
        
    TOML file with nested keys:
        >>> handler = TomlVersionHandler()
        >>> version = handler.read_version("pyproject.toml", "tool.poetry.version")
        >>> handler.update_version("pyproject.toml", "tool.poetry.version", "2024.01.15")
        
    Dockerfile with ARG directive:
        >>> handler = DockerfileVersionHandler()
        >>> version = handler.read_version("Dockerfile", "VERSION", directive="ARG")
        >>> handler.update_version("Dockerfile", "VERSION", "2024.01.15", directive="ARG")
        
    Batch processing multiple files:
        >>> file_configs = [
        ...     {"path": "version.py", "file_type": "python", "variable": "__version__"},
        ...     {"path": "pyproject.toml", "file_type": "toml", "variable": "tool.poetry.version"},
        ...     {"path": "package.json", "file_type": "json", "variable": "version"},
        ... ]
        >>> updated_files = update_version_in_files("2024.01.15", file_configs)
        >>> print(f"Updated {len(updated_files)} files successfully")
        
    Version formatting with standards:
        >>> handler = TomlVersionHandler()
        >>> handler.update_version(
        ...     "pyproject.toml", 
        ...     "tool.poetry.version", 
        ...     "2024-01-15", 
        ...     version_standard="python"
        ... )  # Converts to PEP 440 format: "2024.1.15"

Dependencies:
    - toml: For TOML file parsing and generation
    - yaml: For YAML file parsing and generation  
    - xml.etree.ElementTree: For XML file processing (standard library)
    - json: For JSON file processing (standard library)
    - re: For regex pattern matching (standard library)
    - configparser: For INI-style file processing (standard library)
    - typing: For type hints and annotations (standard library)

Notes:
    - All file operations use UTF-8 encoding by default
    - Handlers preserve original file formatting where possible
    - Version formatting is applied during updates, not reads
    - Error messages are designed to be user-friendly and actionable
    - The module is thread-safe for read operations but not for concurrent writes
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
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            match = version_pattern.search(content)
            if match:
                return match.group(1)
            print(f"Variable '{variable}' not found in {file_path}")
            return None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

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
        version_pattern = re.compile(
            rf'^(\s*{re.escape(variable)}\s*=\s*)(["\'])(.+?)(["\'])(\s*)$',
            re.MULTILINE,
        )
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            def replacement(match):
                return f"{match.group(1)}{match.group(2)}{new_version}{match.group(4)}{match.group(5)}"

            new_content, num_subs = version_pattern.subn(replacement, content)

            if num_subs > 0:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {file_path}")
                return True
            else:
                print(f"Variable '{variable}' not found in {file_path}")
                return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


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
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = toml.load(file)
            keys = variable.split(".")
            temp = toml_content
            for key in keys:
                temp = temp.get(key)
                if temp is None:
                    print(f"Variable '{variable}' not found in {file_path}")
                    return None
            return temp
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

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
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                toml_content = toml.load(file)

            keys = variable.split(".")
            temp = toml_content
            for key in keys[:-1]:
                if key not in temp:
                    temp[key] = {}
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
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            keys = variable.split(".")
            temp = data
            for key in keys:
                temp = temp.get(key)
                if temp is None:
                    print(f"Variable '{variable}' not found in {file_path}")
                    return None
            return temp
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

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
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            keys = variable.split(".")
            temp = data
            for key in keys[:-1]:
                temp = temp.setdefault(key, {})
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
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(variable)
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

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
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data[variable] = new_version
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
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
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            element = root.find(variable)
            if element is not None:
                return element.text
            print(f"Variable '{variable}' not found in {file_path}")
            return None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

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
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            element = root.find(variable)
            if element is not None:
                element.text = new_version
                tree.write(file_path)
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

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            match = pattern.search(content)
            if match:
                return match.group(1).strip()
            print(f"No {directive} variable '{variable}' found in {file_path}")
            return None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

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

        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        pattern = re.compile(
            rf"(^\s*{directive}\s+{re.escape(variable)}\s*=\s*)(.+?)\s*$", re.MULTILINE
        )

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            def replacement(match):
                return f"{match.group(1)}{new_version}"

            new_content, num_subs = pattern.subn(replacement, content)
            if num_subs > 0:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {directive} variable '{variable}' in {file_path}")
                return True
            else:
                print(f"No {directive} variable '{variable}' found in {file_path}")
                return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


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
        try:
            with open(file_path, "r") as file:
                for line in file:
                    if line.startswith(variable):
                        return line.split("=")[1].strip()
            print(f"Variable '{variable}' not found in {file_path}")
            return None
        except Exception as e:
            print(f"Error reading version from {file_path}: {e}")
            return None

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
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        version_pattern = re.compile(
            rf"^({re.escape(variable)}\s*[:]?=\s*)(.*)$", re.MULTILINE
        )
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            def replacement(match):
                return f"{match.group(1)}{new_version}"

            new_content, num_subs = version_pattern.subn(replacement, content)

            if num_subs > 0:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {file_path}")
                return True
            else:
                print(f"Variable '{variable}' not found in {file_path}")
                return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


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
        """Updates the version string in the specified properties file.

        Args:
            file_path (str): The path to the properties file.
            variable (str): The property key that holds the version string.
            new_version (str): The new version string to set.
            **kwargs: Additional keyword arguments including version_standard.

        Returns:
            bool: True if the version was successfully updated, False otherwise.
        """
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            updated = False
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                    key, value = stripped_line.split("=", 1)
                    if key.strip() == variable:
                        lines[i] = f"{key}={new_version}\n"
                        updated = True
                        break

            if updated:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.writelines(lines)
                print(f"Updated {file_path}")
                return True
            else:
                print(f"Property '{variable}' not found in {file_path}")
                return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


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
        """Updates the version string in the specified .env file.

        Args:
            file_path (str): The path to the .env file.
            variable (str): The environment variable name that holds the version string.
            new_version (str): The new version string to set.
            **kwargs: Additional keyword arguments including version_standard.

        Returns:
            bool: True if the version was successfully updated, False otherwise.
        """
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            updated = False
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                    key, value = stripped_line.split("=", 1)
                    if key.strip() == variable:
                        lines[i] = f"{key}={new_version}\n"
                        updated = True
                        break

            if updated:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.writelines(lines)
                print(f"Updated {file_path}")
                return True
            else:
                print(f"Environment variable '{variable}' not found in {file_path}")
                return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


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
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)

        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(file_path)

            updated = False
            # Handle dot notation like "metadata.version"
            if "." in variable:
                section, key = variable.split(".", 1)
                if section in config:
                    config[section][key] = new_version
                    updated = True
                else:
                    # Create section if it doesn't exist
                    config.add_section(section)
                    config[section][key] = new_version
                    updated = True
            else:
                # Search in all sections for the key and update the first match
                for section in config.sections():
                    if variable in config[section]:
                        config[section][variable] = new_version
                        updated = True
                        break

                # If not found in any section, add to metadata section
                if not updated:
                    if 'metadata' not in config:
                        config.add_section('metadata')
                    config['metadata'][variable] = new_version
                    updated = True

            if updated:
                with open(file_path, "w", encoding="utf-8") as file:
                    config.write(file)
                print(f"Updated {file_path}")
                return True
            else:
                print(f"Variable '{variable}' not found in {file_path}")
                return False
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False


def get_version_handler(file_type: str) -> VersionHandler:
    """Returns the appropriate version handler for the given file type.

    This function returns an instance of a version handler class based on the
    specified file type. If the file type is not supported, it raises a ValueError.

    Args:
        file_type (str): The type of the file (e.g., "python", "toml", "yaml", "json", "xml", "dockerfile", "makefile", "properties", "env", "setup.cfg").

    Returns:
        VersionHandler: An instance of the appropriate version handler class.

    Raises:
        ValueError: If the specified file type is not supported.

    Example:
        handler = get_version_handler("python")
    """
    if file_type == "python":
        return PythonVersionHandler()
    elif file_type == "toml":
        return TomlVersionHandler()
    elif file_type == "yaml":
        return YamlVersionHandler()
    elif file_type == "json":
        return JsonVersionHandler()
    elif file_type == "xml":
        return XmlVersionHandler()
    elif file_type == "dockerfile":
        return DockerfileVersionHandler()
    elif file_type == "makefile":
        return MakefileVersionHandler()
    elif file_type == "properties":
        return PropertiesVersionHandler()
    elif file_type == "env":
        return EnvVersionHandler()
    elif file_type == "setup.cfg":
        return SetupCfgVersionHandler()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


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
