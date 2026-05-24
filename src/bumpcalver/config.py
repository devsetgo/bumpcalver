"""
Configuration loader for BumpCalver.

This module provides functionality to load configuration settings for BumpCalver
from either a `pyproject.toml` or `bumpcalver.toml` file. The configuration
includes settings for version format, timezone, file configurations, Git tagging,
and auto-commit.

The primary configuration file is `pyproject.toml`. If it is not found, the module
will look for `bumpcalver.toml`.

Functions:
    load_config: Loads the configuration settings from the configuration file.

Example:
    config = load_config()
    print(config["version_format"])
"""

import os
import sys
from typing import Any, Dict

import toml

from .utils import default_timezone, parse_dot_path


def load_config() -> Dict[str, Any]:
    config: Dict[str, Any] = {}

    config_file = None
    if os.path.exists("pyproject.toml"):
        config_file = "pyproject.toml"
    elif os.path.exists("bumpcalver.toml"):
        config_file = "bumpcalver.toml"

    if config_file:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                loaded_config: Dict[str, Any] = toml.load(f)

            if config_file == "pyproject.toml":
                bumpcalver_config: Dict[str, Any] = loaded_config.get("tool", {}).get(
                    "bumpcalver", {}
                )
            else:
                bumpcalver_config: Dict[str, Any] = loaded_config

            config["version_format"] = bumpcalver_config.get(
                "version_format", "{current_date}-{build_count:03}"
            )
            config["date_format"] = bumpcalver_config.get("date_format", "%Y.%m.%d")
            config["timezone"] = bumpcalver_config.get("timezone", default_timezone)
            config["file_configs"] = bumpcalver_config.get("file", [])
            config["git_tag"] = bumpcalver_config.get("git_tag", False)
            config["auto_commit"] = bumpcalver_config.get("auto_commit", False)
            config["major"] = bumpcalver_config.get("major", 0)
            config["minor"] = bumpcalver_config.get("minor", 0)
            config["patch"] = bumpcalver_config.get("patch", 0)
            config["beta_format"] = bumpcalver_config.get("beta_format", ".beta")
            config["rc_format"] = bumpcalver_config.get("rc_format", ".rc")
            config["release_format"] = bumpcalver_config.get("release_format", ".release")

            for file_config in config["file_configs"]:
                original_path = file_config["path"]
                file_type = file_config.get("file_type", "")
                file_config["path"] = parse_dot_path(original_path, file_type)
                print(
                    f"Original path: {original_path} -> Converted path: {file_config['path']}"
                )

        except toml.TomlDecodeError as e:
            print(f"Error decoding {config_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(
                f"Error loading configuration from {config_file}: {e}", file=sys.stderr
            )
    else:
        print(
            "No configuration file found. Please create either pyproject.toml or bumpcalver.toml.",
            file=sys.stderr,
        )

    return config
