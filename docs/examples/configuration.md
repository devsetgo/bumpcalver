# Library Configuration Examples
Pyproject.toml is the preferred method, but there is an example for the bumpcalver.toml configuration included also.

## PyProject.TOML

Add to your pyproject.toml

```toml
[project]
name = "example PyProject.toml"
version = "2025.2.2"
requires-python = ">=3.10"
description = "A powerful CLI tool for effortless calendar-based version management"
keywords = [ "cli", "tool", "calendar", "version", "management", "configuration", "example",]
readme = "README.md"

[project.license]
file = "LICENSE"

[tool.bumpcalver]
version_format = "{current_date}-{build_count:03}"
date_format = "%y.%m.%d"
timezone = "America/New_York"
git_tag = true
auto_commit = true
[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "examples/makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "examples/dockerfile"
file_type = "dockerfile"
variable = "arg.VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "examples/dockerfile"
file_type = "dockerfile"
variable = "env.APP_VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "examples/p.py"
file_type = "python"
variable = "__version__"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "sonar-project.properties"
file_type = "properties"
variable = "sonar.projectVersion"
version_standard = "default"

[[tool.bumpcalver.file]]
path = ".env"
file_type = "env"
variable = "VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "setup.cfg"
file_type = "setup.cfg"
variable = "metadata.version"
version_standard = "python"


```


## BumpCalver.TOML Configuration

File needs to be in the root and named bumpcalver.toml

```toml
version_format = "{current_date}-{build_count:03}"
date_format = "%y.%m.%d"
timezone = "America/New_York"
git_tag = true
auto_commit = true

[[file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"

[[file]]
path = "examples/makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"

[[file]]
path = "examples/dockerfile"
file_type = "dockerfile"
variable = "arg.VERSION"
version_standard = "default"

[[file]]
path = "examples/dockerfile"
file_type = "dockerfile"
variable = "env.APP_VERSION"
version_standard = "default"

[[file]]
path = "examples/p.py"
file_type = "python"
variable = "__version__"
version_standard = "python"

[[file]]
path = "sonar-project.properties"
file_type = "properties"
variable = "sonar.projectVersion"
version_standard = "default"

[[file]]
path = ".env"
file_type = "env"
variable = "VERSION"
version_standard = "default"

[[file]]
path = "setup.cfg"
file_type = "setup.cfg"
variable = "metadata.version"
version_standard = "python"
```
