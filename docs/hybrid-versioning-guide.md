# Hybrid Semantic + Calendar Versioning Guide

## Overview

BumpCalver supports **hybrid versioning** — version strings that combine a Semantic Versioning (SemVer) prefix with a Calendar Versioning (CalVer) date and build count.

A hybrid version communicates two things at once:

- **The semantic prefix** (`1.0`, `2.3.1`) signals project maturity and compatibility, just like SemVer.
- **The calendar suffix** (`20260523.1`) shows exactly when the release was made, just like CalVer.

Example: `1.0-20260523.1`

---

## Why Use Hybrid Versioning?

| Versioning Style | Strength | Weakness |
|-----------------|----------|----------|
| Pure SemVer (`1.4.2`) | Communicates stability and compatibility | No release-date context |
| Pure CalVer (`2026.05.23.1`) | Shows when a release happened | No maturity signal |
| **Hybrid (`1.0-20260523.1`)** | Both signals in one string | Slightly longer version string |

Hybrid versioning is a practical choice for:

- **Libraries** that want to signal production readiness (`1.0`) while keeping release dates visible.
- **Long-running projects** that keep a stable API but release frequently.
- **Teams migrating from SemVer** who want to add temporal context without abandoning familiar version milestones.

---

## Format Placeholders

Hybrid versioning adds three new placeholders alongside the existing `{current_date}` and `{build_count}`:

| Placeholder | Description | Source |
|-------------|-------------|--------|
| `{major}` | Major version component | `major` key in config |
| `{minor}` | Minor version component | `minor` key in config |
| `{patch}` | Patch version component | `patch` key in config |
| `{current_date}` | Today's date, formatted by `date_format` | Computed at runtime |
| `{build_count}` | Incrementing build number | Computed at runtime |

When any of `{major}`, `{minor}`, or `{patch}` appear in `version_format`, BumpCalver enters hybrid mode and includes the semantic prefix in the generated version.

---

## Configuration

Add `major`, `minor`, `patch` keys to the `[tool.bumpcalver]` section alongside your existing settings:

```toml
[tool.bumpcalver]
major = 1
minor = 0
patch = 0
version_format = "{major}.{minor}-{current_date}.{build_count}"
date_format = "%Y%m%d"
timezone = "America/New_York"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"

[[tool.bumpcalver.file]]
path = "src/mypackage/__init__.py"
file_type = "python"
variable = "__version__"
```

Or in a standalone `bumpcalver.toml`:

```toml
major = 1
minor = 0
patch = 0
version_format = "{major}.{minor}-{current_date}.{build_count}"
date_format = "%Y%m%d"
timezone = "America/New_York"

[[file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
```

---

## Supported Format Examples

Any combination of semantic placeholders, separators, date formats, and build count formatting is supported:

| `version_format` | `date_format` | Example output |
|-----------------|--------------|----------------|
| `{major}.{minor}-{current_date}.{build_count}` | `%Y%m%d` | `1.0-20260523.1` |
| `{major}.{minor}.{patch}-{current_date}.{build_count:03}` | `%Y%m%d` | `1.0.0-20260523.001` |
| `{major}.{minor}-{current_date}.{build_count:03}` | `%Y.%m.%d` | `1.0-2026.05.23.001` |
| `{major}.{minor}-{current_date}-{build_count:02}` | `%Y%m%d` | `2.3-20260523-01` |
| `{major}.{minor}-{current_date}.{build_count}` | `%y.Q%q` | `1.0-26.Q2.5` |
| `{major}.{minor}.{patch}-{current_date}.{build_count}` | `%Y%m%d` | `2.3.4-20260523.10` |

---

## CLI Usage

### Generating a hybrid version

Use `--build` just as you would for pure CalVer:

```bash
bumpcalver --build
# → 1.0-20260523.1
```

Run again the same day:

```bash
bumpcalver --build
# → 1.0-20260523.2   (build count increments)
```

Run on a new day:

```bash
bumpcalver --build
# → 1.0-20260524.1   (date changes, count resets to 1)
```

### Bumping the semantic prefix

Use `--bump` to increment a semantic component. The new value is written back to `pyproject.toml` (or `bumpcalver.toml`) automatically so the next plain `--build` continues from the updated baseline.

```bash
# Increment minor version: minor 0→1, patch resets to 0
bumpcalver --build --bump minor
# Config updated: minor = 1, patch = 0
# → 1.1-20260523.1

# Increment major version: major 1→2, minor and patch reset to 0
bumpcalver --build --bump major
# Config updated: major = 2, minor = 0, patch = 0
# → 2.0-20260523.1

# Increment patch version
bumpcalver --build --bump patch
# Config updated: patch = 1
# → 1.0-20260523.1  (with {patch} in format: 1.0.1-20260523.1)
```

`--bump` accepts `major`, `minor`, or `patch` as values:

```
--bump [major|minor|patch]   Increment the specified semantic version
                              component in config
```

### Combining with other options

All existing options work alongside `--bump`:

```bash
# Bump minor and tag the release
bumpcalver --build --bump minor --git-tag --auto-commit

# Create a release candidate at a new minor version
bumpcalver --build --bump minor --rc
# → 1.1-20260523.1.rc
```

---

## How Build Count Increment Works

When you run `bumpcalver --build` with a hybrid format, the library:

1. Reads the current version from the first configured file (e.g., `1.0-20260522.4`).
2. Uses the `version_format` as a regex template to extract the **date part** (`20260522`) and **build count** (`4`).
3. Compares the extracted date to today.
   - **Same day** → build count increments by 1.
   - **Different day** → build count resets to 1.
4. Applies the `major`, `minor`, `patch` values from config (unchanged unless `--bump` was used).
5. Formats and writes the new version: `1.0-20260523.1`.

The semantic prefix is **never parsed or incremented automatically** — it only comes from the config values.

---

## Pre-release Suffixes

Hybrid versions work with all existing suffix options:

```bash
bumpcalver --build --beta
# → 1.0-20260523.1.beta

bumpcalver --build --rc
# → 1.0-20260523.1.rc

bumpcalver --build --custom alpha
# → 1.0-20260523.1.alpha
```

---

## PEP 440 Considerations

When `version_standard = "python"` is set on a file, BumpCalver applies PEP 440 normalization (converts hyphens to dots, removes leading zeros). A hybrid version like `1.0-20260523.1` would become `1.0.20260523.1`.

If you want to preserve the hyphen separator, either:

- Omit `version_standard` (defaults to `"default"`, no transformation).
- Use a dot separator in your format: `{major}.{minor}.{current_date}.{build_count}` → `1.0.20260523.1`.

---

## Best Practices

### 1. Keep the semantic prefix stable between releases

The `major`, `minor`, and `patch` values in config are your deliberate milestones. Only update them when you intentionally want to signal a compatibility or maturity change — not on every build.

### 2. Use `--bump` when the API changes

```bash
# Breaking change → bump major
bumpcalver --build --bump major --git-tag --auto-commit

# New backward-compatible feature → bump minor
bumpcalver --build --bump minor --git-tag --auto-commit
```

### 3. Choose a separator that fits your ecosystem

```toml
# Hyphen (most common hybrid separator)
version_format = "{major}.{minor}-{current_date}.{build_count}"

# Dot only (PEP 440 safe)
version_format = "{major}.{minor}.{current_date}.{build_count}"
```

### 4. Pad the build count for consistent sort order

```toml
version_format = "{major}.{minor}-{current_date}.{build_count:03}"
# → 1.0-20260523.001 instead of 1.0-20260523.1
```

---

## Troubleshooting

### Version not parsing on next build

If the format stored in a file does not match the current `version_format`, parsing fails and the build count resets to 1. This is safe — the tool logs a message and continues. It commonly happens when:

- You changed `version_format` after the last build.
- You manually edited the version string.

### Semantic values showing as 0

If `major`, `minor`, or `patch` are not set in config, they default to `0`. Add them explicitly:

```toml
[tool.bumpcalver]
major = 1
minor = 0
patch = 0
```

### `--bump` not persisting to config

`--bump` writes back to `pyproject.toml` or `bumpcalver.toml` using regex matching. It requires the key to already exist in the file. If the key is absent, add it manually first.

---

## See Also

- [Calendar Versioning Guide](calendar-versioning-guide.md) — pure CalVer patterns and date formats
- [Configuration Examples](examples/configuration.md) — full configuration reference
- [Undo Operations](undo.md) — reverting version bumps
