Python:

[![PyPI version fury.io](https://badge.fury.io/py/bumpcalver.svg)](https://pypi.python.org/pypi/bumpcalver/)
[![Downloads](https://static.pepy.tech/badge/bumpcalver)](https://pepy.tech/project/bumpcalver)
[![Downloads](https://static.pepy.tech/badge/bumpcalver/month)](https://pepy.tech/project/bumpcalver)
[![Downloads](https://static.pepy.tech/badge/bumpcalver/week)](https://pepy.tech/project/bumpcalver)

Support Python Versions

![Static Badge](https://img.shields.io/badge/Python-3.12%20%7C%203.11%20%7C%203.10%20-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

CI/CD Pipeline:

[![Testing - Main](https://github.com/devsetgo/bumpcalver/actions/workflows/testing.yml/badge.svg?branch=main)](https://github.com/devsetgo/bumpcalver/actions/workflows/testing.yml)
[![Testing - Dev](https://github.com/devsetgo/bumpcalver/actions/workflows/testing.yml/badge.svg?branch=dev)](https://github.com/devsetgo/bumpcalver/actions/workflows/testing.yml)

SonarCloud:

[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_bumpcalver&metric=coverage)](https://sonarcloud.io/dashboard?id=devsetgo_bumpcalver)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_bumpcalver&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=devsetgo_bumpcalver)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_bumpcalver&metric=alert_status)](https://sonarcloud.io/dashboard?id=devsetgo_bumpcalver)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_bumpcalver&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=devsetgo_bumpcalver)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=devsetgo_bumpcalver&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=devsetgo_bumpcalver)



# BumpCalver CLI Documentation

## Overview

The **BumpCalver CLI** is a command-line interface for calendar-based version bumping. It automates the process of updating version strings in your project's files based on the current date and build count. Additionally, it can create Git tags and commit changes automatically. The CLI is highly configurable via a `pyproject.toml` file and supports various customization options to fit your project's needs.

---

## Table of Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
  - [Example Configuration](#example-configuration)
- [Command-Line Usage](#command-line-usage)
  - [Options](#options)
- [Examples](#examples)


---

## Installation

To install the BumpCalver CLI, you can add it to your project's dependencies. If it's packaged as a Python module, you might install it via:

```bash
pip install bumpcalver
```

*Note: Replace the installation command with the actual method based on how the package is distributed.*

---

## Getting Started

1. **Configure Your Project**: Create or update the `pyproject.toml` file in your project's root directory to include the `[tool.bumpcalver]` section with your desired settings.

2. **Run the CLI**: Use the `bumpcalver` command with appropriate options to bump your project's version.

Example:

```bash
bumpcalver --build --git-tag --auto-commit
```

---

## Configuration

The BumpCalver CLI relies on a `pyproject.toml` configuration file located at the root of your project. This file specifies how versioning should be handled, which files to update, and other settings.

### Configuration Options

- `version_format` (string): Format string for the version. Should include `{current_date}` and `{build_count}` placeholders.
- `timezone` (string): Timezone for date calculations (e.g., `UTC`, `America/New_York`).
- `file` (list of tables): Specifies which files to update and how to find the version string.
  - `path` (string): Path to the file to be updated.
  - `variable` (string, optional): The variable name that holds the version string in the file.
  - `pattern` (string, optional): A regex pattern to find the version string.
- `git_tag` (boolean): Whether to create a Git tag with the new version.
- `auto_commit` (boolean): Whether to automatically commit changes when creating a Git tag.

### Example Configuration

```toml
[tool.bumpcalver]
version_format = "{current_date}-{build_count:03}"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "version.py"
variable = "__version__"
```

---

## Command-Line Usage

The CLI provides several options to customize the version bumping process.

```bash
Usage: bumpcalver [OPTIONS]

Options:
  --beta                      Use beta versioning.
  --build                     Use build count versioning.
  --timezone TEXT             Timezone for date calculations (default: value
                              from config or America/New_York).
  --git-tag / --no-git-tag    Create a Git tag with the new version.
  --auto-commit / --no-auto-commit
                              Automatically commit changes when creating a Git
                              tag.
  --help                      Show this message and exit.
```

### Options

- `--beta`: Prefixes the version with `beta-`.
- `--build`: Increments the build count based on the current date.
- `--timezone`: Overrides the timezone specified in the configuration.
- `--git-tag` / `--no-git-tag`: Forces Git tagging on or off, overriding the configuration.
- `--auto-commit` / `--no-auto-commit`: Forces auto-commit on or off, overriding the configuration.

---

## Examples

### Basic Version Bump

To bump the version using the current date and build count:

```bash
bumpcalver --build
```

### Beta Versioning

To create a beta version:

```bash
bumpcalver --build --beta
```

### Specifying Timezone

To use a specific timezone:

```bash
bumpcalver --build --timezone Europe/London
```

### Creating a Git Tag with Auto-Commit

To bump the version, commit changes, and create a Git tag:

```bash
bumpcalver --build --git-tag --auto-commit
```

---

## Error Handling

- **Unknown Timezone**: If an invalid timezone is specified, the default timezone (`America/New_York`) is used, and a warning is printed.

- **File Not Found**: If a specified file is not found during version update, an error message is printed.

- **Invalid Build Count**: If the existing build count in a file is invalid, it resets to `1`, and a warning is printed.

- **Git Errors**: Errors during Git operations are caught, and an error message is displayed.

- **Malformed Configuration**: If the `pyproject.toml` file is malformed, an error is printed, and the program exits.

---

## Support

For issues or questions, please open an issue on the project's repository.

---
