from typing import Any, Optional

from bumpcalver.handlers import VersionHandler


class IniVersionHandler(VersionHandler):
    """Example plugin handler for INI-style `KEY = value` files.

    Registered as the "ini" file_type via this package's entry point
    (see pyproject.toml). Reuses the base class's key=value helpers, the
    same way the built-in PropertiesVersionHandler/EnvVersionHandler do.
    """

    def read_version(self, file_path: str, variable: str, **kwargs: Any) -> Optional[str]:
        return self._read_key_value_file(file_path, variable)

    def update_version(
        self, file_path: str, variable: str, new_version: str, **kwargs: Any
    ) -> bool:
        new_version = self._format_version_with_standard(new_version, **kwargs)
        return self._update_key_value_file(file_path, variable, new_version, "Setting")
