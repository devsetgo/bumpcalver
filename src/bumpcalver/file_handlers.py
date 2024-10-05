# # src/bumpcalver/file_handlers.py
# import json
# import re
# import xml.etree.ElementTree as ET
# from abc import ABC, abstractmethod
# from typing import Optional

# import toml
# import yaml


# class VersionHandler(ABC):
#     @abstractmethod
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         pass

#     @abstractmethod
#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         pass


# class PythonVersionHandler(VersionHandler):
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         version_pattern = re.compile(
#             rf'^\s*{re.escape(variable)}\s*=\s*["\'](.+?)["\']\s*$', re.MULTILINE
#         )
#         try:
#             with open(file_path, "r") as file:
#                 content = file.read()
#             match = version_pattern.search(content)
#             return match.group(1) if match else None
#         except Exception as e:
#             print(f"Error reading version from {file_path}: {e}")
#             return None

#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         version_pattern = re.compile(
#             rf'^(\s*{re.escape(variable)}\s*=\s*)(["\'])(.+?)(["\'])\s*$', re.MULTILINE
#         )
#         try:
#             with open(file_path, "r", encoding="utf-8") as file:
#                 content = file.read()
#             new_content, num_subs = version_pattern.subn(
#                 rf"\1\2{new_version}\4", content
#             )
#             if num_subs > 0:
#                 with open(file_path, "w", encoding="utf-8") as file:
#                     file.write(new_content)
#                 return True
#             return False
#         except Exception as e:
#             print(f"Error updating {file_path}: {e}")
#             return False


# class TomlVersionHandler(VersionHandler):
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         try:
#             with open(file_path, "r") as f:
#                 data = toml.load(f)
#             return data.get(variable)
#         except Exception as e:
#             print(f"Error reading version from {file_path}: {e}")
#             return None

#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         try:
#             with open(file_path, "r", encoding="utf-8") as f:
#                 data = toml.load(f)
#             data[variable] = new_version
#             with open(file_path, "w", encoding="utf-8") as f:
#                 toml.dump(data, f)
#             return True
#         except Exception as e:
#             print(f"Error updating {file_path}: {e}")
#             return False


# class YamlVersionHandler(VersionHandler):
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         try:
#             with open(file_path, "r") as f:
#                 data = yaml.safe_load(f)
#             return data.get(variable)
#         except Exception as e:
#             print(f"Error reading version from {file_path}: {e}")
#             return None

#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         try:
#             with open(file_path, "r", encoding="utf-8") as f:
#                 data = yaml.safe_load(f)
#             data[variable] = new_version
#             with open(file_path, "w", encoding="utf-8") as f:
#                 yaml.safe_dump(data, f)
#             return True
#         except Exception as e:
#             print(f"Error updating {file_path}: {e}")
#             return False


# class JsonVersionHandler(VersionHandler):
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         try:
#             with open(file_path, "r") as f:
#                 data = json.load(f)
#             return data.get(variable)
#         except Exception as e:
#             print(f"Error reading version from {file_path}: {e}")
#             return None

#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         try:
#             with open(file_path, "r", encoding="utf-8") as f:
#                 data = json.load(f)
#             data[variable] = new_version
#             with open(file_path, "w", encoding="utf-8") as f:
#                 json.dump(data, f, indent=2)
#             return True
#         except Exception as e:
#             print(f"Error updating {file_path}: {e}")
#             return False


# class XmlVersionHandler(VersionHandler):
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         try:
#             tree = ET.parse(file_path)
#             root = tree.getroot()
#             element = root.find(variable)
#             return element.text if element is not None else None
#         except Exception as e:
#             print(f"Error reading version from {file_path}: {e}")
#             return None

#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         try:
#             tree = ET.parse(file_path)
#             root = tree.getroot()
#             element = root.find(variable)
#             if element is not None:
#                 element.text = new_version
#                 tree.write(file_path)
#                 return True
#             return False
#         except Exception as e:
#             print(f"Error updating {file_path}: {e}")
#             return False


# class DockerfileVersionHandler(VersionHandler):
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         version_pattern = re.compile(
#             rf"^\s*ARG\s+{re.escape(variable)}\s*=\s*(.+?)\s*$", re.MULTILINE
#         )
#         try:
#             with open(file_path, "r") as file:
#                 content = file.read()
#             match = version_pattern.search(content)
#             return match.group(1) if match else None
#         except Exception as e:
#             print(f"Error reading version from {file_path}: {e}")
#             return None

#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         version_pattern = re.compile(
#             rf"^\s*(ARG\s+{re.escape(variable)}\s*=\s*)(.+?)\s*$", re.MULTILINE
#         )
#         try:
#             with open(file_path, "r", encoding="utf-8") as file:
#                 content = file.read()
#             new_content, num_subs = version_pattern.subn(rf"\1{new_version}", content)
#             if num_subs > 0:
#                 with open(file_path, "w", encoding="utf-8") as file:
#                     file.write(new_content)
#                 return True
#             return False
#         except Exception as e:
#             print(f"Error updating {file_path}: {e}")
#             return False


# class MakefileVersionHandler(VersionHandler):
#     def read_version(self, file_path: str, variable: str) -> Optional[str]:
#         version_pattern = re.compile(
#             rf"^\s*{re.escape(variable)}\s*[:]?=\s*(.+?)\s*$", re.MULTILINE
#         )
#         try:
#             with open(file_path, "r") as file:
#                 content = file.read()
#             match = version_pattern.search(content)
#             return match.group(1) if match else None
#         except Exception as e:
#             print(f"Error reading version from {file_path}: {e}")
#             return None

#     def update_version(self, file_path: str, variable: str, new_version: str) -> bool:
#         version_pattern = re.compile(
#             rf"^\s*({re.escape(variable)}\s*[:]?=\s*)(.+?)\s*$", re.MULTILINE
#         )
#         try:
#             with open(file_path, "r", encoding="utf-8") as file:
#                 content = file.read()
#             new_content, num_subs = version_pattern.subn(rf"\1{new_version}", content)
#             if num_subs > 0:
#                 with open(file_path, "w", encoding="utf-8") as file:
#                     file.write(new_content)
#                 return True
#             return False
#         except Exception as e:
#             print(f"Error updating {file_path}: {e}")
#             return False
