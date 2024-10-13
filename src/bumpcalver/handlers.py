import json
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import toml
import yaml


# Abstract base class for version handlers
class VersionHandler(ABC):
    @abstractmethod
    def read_version(
        self, file_path: str, variable: str, **kwargs
    ) -> Optional[str]:  # pragma: no cover
        pass

    @abstractmethod
    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs
    ) -> bool:  # pragma: no cover
        pass

    def format_version(self, version: str, standard: str) -> str:
        if standard == "python":
            return self.format_pep440_version(version)
        return version

    def format_pep440_version(self, version: str) -> str:
        # Implement PEP 440 formatting rules
        # Replace hyphens and underscores with dots
        version = version.replace("-", ".").replace("_", ".")
        # Ensure no leading zeros in numeric segments
        version = re.sub(r"\b0+(\d)", r"\1", version)
        return version


class PythonVersionHandler(VersionHandler):
    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
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
        version_standard = kwargs.get("version_standard", "default")
        new_version = self.format_version(new_version, version_standard)
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
    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
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
    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
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
    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
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
    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
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
    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
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
    def read_version(self, file_path: str, variable: str, **kwargs) -> Optional[str]:
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


def get_version_handler(file_type: str) -> VersionHandler:
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
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def update_version_in_files(
    new_version: str, file_configs: List[Dict[str, Any]]
) -> List[str]:
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
