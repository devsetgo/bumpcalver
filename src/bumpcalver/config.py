import os
import sys
from typing import Any, Dict

import toml

from .utils import default_timezone, parse_dot_path


def load_config() -> Dict[str, Any]:
    config: Dict[str, Any] = {}

    if os.path.exists("pyproject.toml"):
        try:
            with open("pyproject.toml", "r", encoding="utf-8") as f:
                pyproject: Dict[str, Any] = toml.load(f)

            bumpcalver_config: Dict[str, Any] = pyproject.get("tool", {}).get(
                "bumpcalver", {}
            )

            config["version_format"] = bumpcalver_config.get(
                "version_format", "{current_date}-{build_count:03}"
            )
            config["timezone"] = bumpcalver_config.get("timezone", default_timezone)
            config["file_configs"] = bumpcalver_config.get("file", [])
            config["git_tag"] = bumpcalver_config.get("git_tag", False)
            config["auto_commit"] = bumpcalver_config.get("auto_commit", False)

            # Print paths for debugging
            for file_config in config["file_configs"]:
                original_path = file_config["path"]
                file_type = file_config.get("file_type", "")
                file_config["path"] = parse_dot_path(original_path, file_type)
                print(
                    f"Original path: {original_path} -> Converted path: {file_config['path']}"
                )

        except toml.TomlDecodeError as e:
            print(f"Error parsing pyproject.toml: {e}")
            sys.exit(1)
    else:
        print("pyproject.toml not found. Using default configuration.")

    return config
