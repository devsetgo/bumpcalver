# Calendar Versioning (CalVer) Guide

## Overview

BumpCalver supports a comprehensive range of calendar versioning patterns based on the [CalVer specification](https://calver.org) and real-world industry practices. This guide walks you through the various date formats available and provides practical examples for different use cases.

## What is Calendar Versioning?

Calendar Versioning (CalVer) is a versioning scheme that uses dates as the primary versioning identifier. Unlike Semantic Versioning (SemVer), CalVer provides immediate context about when a release was made, making it ideal for:

- **Regular Release Cycles**: Software released on a schedule (Ubuntu, VS Code)
- **Date-Sensitive Projects**: When knowing the release date is crucial
- **Long-Term Support**: Identifying support lifecycles by date
- **Marketing Alignment**: Aligning technical releases with business timelines

## Supported Date Format Patterns

### Basic Year-Month-Day Patterns

These are the most common calendar versioning patterns:

#### Dot-Separated Formats
```toml
# Ubuntu-style: Short year with month and day
date_format = "%y.%m.%d"  # Example: 24.12.07

# Full year variant
date_format = "%Y.%m.%d"  # Example: 2024.12.07

# Month only (common for regular releases)
date_format = "%y.%m"     # Example: 24.12
date_format = "%Y.%m"     # Example: 2024.12
```

#### Hyphen-Separated Formats (ISO 8601)
```toml
# ISO date format
date_format = "%Y-%m-%d"  # Example: 2024-12-07

# With build count
version_format = "{current_date}-{build_count:03}"
# Result: 2024-12-07-001
```

### Quarter-Based Patterns

Perfect for quarterly releases and business cycles:

```toml
# Short year with quarter
date_format = "%y.Q%q"    # Example: 24.Q4

# Full year with quarter
date_format = "%Y.Q%q"    # Example: 2024.Q4

# With build count
version_format = "{current_date}.{build_count:03}"
# Result: 24.Q4.001
```

### Week-Based Patterns

Ideal for agile development with weekly releases:

```toml
# ISO week numbers
date_format = "%y.%V"     # Example: 24.49 (week 49)
date_format = "%Y.%V"     # Example: 2024.49

# Version with build count
version_format = "{current_date}.{build_count:03}"
# Result: 24.49.001
```

### Day-of-Year Patterns (Julian)

Common in embedded systems and specialized applications:

```toml
# Julian day format
date_format = "%y.%j"     # Example: 24.342 (day 342 of year)
date_format = "%Y.%j"     # Example: 2024.342

# Useful for daily builds
version_format = "{current_date}.{build_count:03}"
# Result: 24.342.001
```

### Compact Formats

No separators for maximum brevity:

```toml
# Compact date formats
date_format = "%y%m%d"    # Example: 241207
date_format = "%Y%m%d"    # Example: 20241207

version_format = "{current_date}.{build_count:03}"
# Result: 241207.001
```

## Real-World Examples

### Ubuntu Style (LTS and Regular Releases)
```toml
[tool.bumpcalver]
version_format = "{current_date}"
date_format = "%y.%m"
# Examples: 24.04, 24.10, 26.04 (LTS)
```

### Microsoft Visual Studio Code
```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m"
# Examples: 2024.11.1, 2024.11.2
```

### Python Twisted Framework
```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%y.%m"
# Examples: 24.3.0, 24.7.0
```

### Business Quarterly Releases
```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:02}"
date_format = "%Y.Q%q"
timezone = "America/New_York"
# Examples: 2024.Q4.01, 2025.Q1.01
```

### Daily Build System
```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:03}"
date_format = "%y.%j"
# Examples: 24.342.001, 24.342.002
```

## Language-Specific Support

### Python Ecosystem

Python packages using CalVer are fully supported with PEP 440 compliance:

```toml
[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"  # Converts hyphens to dots for PEP 440
```

**PEP 440 Transformation**:
- Input: `2024-12-07-001`
- Python Output: `2024.12.7.1`

**Popular Python Projects Using CalVer**:
- **Twisted**: `24.3.0` (YY.M.patch)
- **pip**: `24.3.1` (YY.M.patch)
- **setuptools**: `75.6.0` (YY.M.patch)
- **certifi**: `2024.12.14` (YYYY.MM.DD)

### JavaScript/Node.js Ecosystem

```toml
[[tool.bumpcalver.file]]
path = "package.json"
file_type = "json"
variable = "version"
version_standard = "default"
```

### Docker Images

```toml
[[tool.bumpcalver.file]]
path = "Dockerfile"
file_type = "dockerfile"
variable = "ARG.VERSION"
version_standard = "default"
```

### Make-based Projects

```toml
[[tool.bumpcalver.file]]
path = "Makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"
```

## Advanced Patterns

### Beta/Alpha Releases

BumpCalver automatically handles pre-release suffixes:

```bash
# Create a beta version
bumpcalver --build --beta
# Result: 24.Q4.001.beta

# Create an alpha version
bumpcalver --build --alpha
# Result: 24.Q4.001.alpha
```

### Mixed Separators (Limited Support)

While not fully supported, simple mixed separators work:

```toml
# Limited support for mixed separators
version_format = "{current_date}_{build_count:03}"
date_format = "%Y-%m-%d"
# May produce: 2024-12-07_001
```

### Custom Business Cycles

```toml
# Financial year quarters (example: July start)
version_format = "FY{current_date}.{build_count:02}"
date_format = "%y.Q%q"
timezone = "America/New_York"
# Examples: FY24.Q2.01, FY24.Q3.01
```

## Choosing the Right Format

### Consider Your Release Cycle

| Release Frequency | Recommended Pattern | Example |
|------------------|-------------------|---------|
| **Monthly** | `%Y.%m` | `2024.12` |
| **Quarterly** | `%y.Q%q` | `24.Q4` |
| **Weekly** | `%y.%V` | `24.49` |
| **Daily** | `%y.%j` | `24.342` |
| **Multiple Daily** | `%y.%m.%d` | `24.12.07` |

### Consider Your Audience

| Audience | Recommended Pattern | Reasoning |
|----------|-------------------|-----------|
| **End Users** | `%Y.%m` | Clear, human-readable |
| **Developers** | `%y.%m.%d` | Detailed, compact |
| **Enterprise** | `%Y.Q%q` | Aligns with business quarters |
| **CI/CD Systems** | `%y.%j` | Daily builds, sequential |

### Consider Your Ecosystem

| Language/Platform | Considerations |
|------------------|----------------|
| **Python** | Use `version_standard = "python"` for PEP 440 |
| **Node.js** | Standard dot notation works well |
| **Docker** | Short formats recommended for tags |
| **Git Tags** | Avoid special characters, prefer dots/hyphens |

## Best Practices

### 1. Consistency
```toml
# Good: Consistent separator usage
date_format = "%y.%m.%d"
version_format = "{current_date}.{build_count:03}"

# Avoid: Mixed separators
version_format = "{current_date}-{build_count:03}"  # Different separator
```

### 2. Timezone Awareness
```toml
# Always specify timezone for distributed teams
timezone = "UTC"                    # Global teams
timezone = "America/New_York"       # US East Coast
timezone = "Europe/London"          # UK/EU
```

### 3. Build Count Padding
```toml
# Good: Consistent width for sorting
version_format = "{current_date}.{build_count:03}"  # 001, 002, 010
version_format = "{current_date}.{build_count:02}"  # 01, 02, 10

# Avoid: Variable width
version_format = "{current_date}.{build_count}"     # 1, 2, 10 (poor sorting)
```

### 4. Documentation
```toml
# Document your versioning strategy
[tool.bumpcalver]
# Strategy: Quarterly releases with weekly build counts
# Format: YY.QQ.BBB (Year.Quarter.Build)
# Example: 24.Q4.001 = Q4 2024, first build
version_format = "{current_date}.{build_count:03}"
date_format = "%y.Q%q"
```

## Validation and Testing

BumpCalver includes comprehensive validation for calendar versioning patterns:

```python
# The system validates:
# ✅ Year components (2-4 digits)
# ✅ Date format consistency
# ✅ Build count extraction
# ✅ Pre-release suffix handling
# ❌ Invalid formats (v1.0.0, release-1.0)
```

### Testing Your Format

```bash
# Test your configuration without making changes
bumpcalver --build --dry-run

# Check current version parsing
bumpcalver --list-history
```

## Troubleshooting

### Common Issues

1. **Mixed Separators Not Working**
   ```
   Error: Version '2024-12-07_001' does not match format
   Solution: Use consistent separators throughout
   ```

2. **Invalid Year Format**
   ```
   Error: Version 'v24.12.001' rejected
   Solution: Remove prefixes, ensure year starts version
   ```

3. **Quarter Format Not Recognized**
   ```
   Error: %q not recognized
   Solution: Use %y.Q%q format, ensure Q is literal
   ```

### Getting Help

- Check the [examples directory](../examples/) for working configurations
- Review the [test suite](tests/test_calver_comprehensive.py) for validated patterns
- Open an issue on [GitHub](https://github.com/devsetgo/bumpcalver/issues) for support

---

*This guide covers the comprehensive calendar versioning capabilities of BumpCalver. For more specific use cases or custom requirements, please refer to the API documentation or reach out to the community.*
