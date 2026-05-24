# Configuration Recipes

Each recipe below is a ready-to-copy starter for a specific language or workflow. Every recipe shows:

- The `[tool.bumpcalver]` block to add to `pyproject.toml` (or `bumpcalver.toml`)
- The `[[tool.bumpcalver.file]]` entries for the files to update
- An example version string the recipe produces

Working copies of the version-bearing files referenced below live in the [`examples/`](https://github.com/devsetgo/bumpcalver/tree/main/examples) directory of the repository. See [File Layout Examples](filelayout.md) for the full catalog.

> **Using `bumpcalver.toml` instead of `pyproject.toml`?**
> Drop the `[tool.bumpcalver]` wrapper and `[[tool.bumpcalver.file]]` prefix — use bare key/value sections with `[[file]]` instead. See [Standalone bumpcalver.toml](#standalone-bumpcalvertoml) at the bottom.

---

## Pure CalVer Recipes

### Python Package

**Produces:** `26.05.24.001`
**Updates:** `pyproject.toml` project version + package `__init__.py`

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:03}"
date_format = "%y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "src/mypackage/__init__.py"
file_type = "python"
variable = "__version__"
version_standard = "python"
```

`__init__.py` before → after:
```python
__version__ = "0.1.0"
__version__ = "26.05.24.001"
```

---

### Node.js / JavaScript

**Produces:** `2026.05.24.1`
**Updates:** `package.json`

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "package.json"
file_type = "json"
variable = "version"
version_standard = "default"
```

`package.json` before → after:
```json
{ "version": "1.0.0" }
{ "version": "2026.05.24.1" }
```

> The `json` handler updates the **top-level** key named by `variable`. Nested keys are not supported.

---

### Rust

**Produces:** `2026.05.24.1`
**Updates:** `Cargo.toml`

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "Cargo.toml"
file_type = "toml"
variable = "package.version"
version_standard = "default"
```

`Cargo.toml` before → after:
```toml
[package]
version = "0.1.0"

[package]
version = "2026.05.24.1"
```

---

### Java — Gradle

**Produces:** `2026.05.24.1`
**Updates:** `gradle.properties`

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "gradle.properties"
file_type = "properties"
variable = "version"
version_standard = "default"
```

`gradle.properties` before → after:
```properties
version=1.0.0
version=2026.05.24.1
```

Reference it in `build.gradle`:
```groovy
version = project.findProperty('version')
```

---

### Java — Maven

**Produces:** `2026.05.24.1`
**Updates:** `version.properties` (imported by Maven)

Maven's `pom.xml` uses XML namespaces that complicate direct editing. The recommended pattern is a dedicated properties file that the Properties Maven Plugin imports at build time:

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "version.properties"
file_type = "properties"
variable = "project.version"
version_standard = "default"
```

`version.properties`:
```properties
project.version=2026.05.24.1
```

Load it in `pom.xml` with the Properties Maven Plugin:
```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>properties-maven-plugin</artifactId>
  <version>1.2.1</version>
  <executions>
    <execution>
      <phase>initialize</phase>
      <goals><goal>read-project-properties</goal></goals>
      <configuration>
        <files><file>version.properties</file></files>
      </configuration>
    </execution>
  </executions>
</plugin>
```

Then reference `${project.version}` in your POM as normal.

---

### Go

**Produces:** `2026.05.24.001`
**Updates:** `Makefile` + `version.txt`

Go's `const`/`var` keyword before the identifier prevents direct matching, so the idiomatic pattern is a `Makefile` variable (passed via `-ldflags`) combined with an embedded `version.txt` file.

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:03}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "Makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "version.txt"
file_type = "env"
variable = "VERSION"
version_standard = "default"
```

`Makefile`:
```makefile
APP_VERSION = 2026.05.24.001

build:
	go build -ldflags="-X main.Version=$(APP_VERSION)" ./...
```

`version.txt`:
```
VERSION=2026.05.24.001
```

Embed `version.txt` in Go code:
```go
import (
    _ "embed"
    "strings"
)

//go:embed version.txt
var versionFile string

var Version = strings.TrimPrefix(strings.TrimSpace(versionFile), "VERSION=")
```

---

### Ruby Gem

**Produces:** `2026.05.24.1`
**Updates:** `lib/mygem/version.rb`

The `python` file type matches any `VARIABLE = "value"` assignment at line start, which covers Ruby constants.

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "lib/mygem/version.rb"
file_type = "python"
variable = "VERSION"
version_standard = "default"
```

`version.rb` before → after:
```ruby
module MyGem
  VERSION = "1.0.0"
end

module MyGem
  VERSION = "2026.05.24.1"
end
```

---

### .NET / C#

**Produces:** `2026.05.24.1`
**Updates:** `MyApp.csproj`

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "MyApp.csproj"
file_type = "xml"
variable = "PropertyGroup/Version"
version_standard = "default"
```

`MyApp.csproj` before → after:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <Version>1.0.0</Version>
  </PropertyGroup>
</Project>
```

> The `xml` handler accepts simple XPath paths. `PropertyGroup/Version` finds `<Version>` nested directly under `<PropertyGroup>` at the document root.

---

### Docker / Container Image

**Produces:** `2026.05.24.1`
**Updates:** `Dockerfile` ARG and ENV in a single pass

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%Y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "Dockerfile"
file_type = "dockerfile"
variable = "arg.VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "Dockerfile"
file_type = "dockerfile"
variable = "env.APP_VERSION"
version_standard = "default"
```

`Dockerfile` before → after:
```dockerfile
ARG VERSION=1.0.0
ENV APP_VERSION=1.0.0

ARG VERSION=2026.05.24.1
ENV APP_VERSION=2026.05.24.1
```

> Prefix with `arg.` for `ARG` instructions and `env.` for `ENV` instructions. The same file can appear twice in the config to update both.

---

## Hybrid Recipes (Semantic Prefix + Calendar Date)

These recipes combine a SemVer prefix (`1.0`, `2.3.1`) with a CalVer date to signal both project maturity and release timing in one string. See the [Hybrid Versioning Guide](../hybrid-versioning-guide.md) for the full reference.

---

### Python Library — Stable API

**Produces:** `1.0-20260524.1`
**Use case:** A library with a stable public API that releases frequently. The `1.0` prefix signals compatibility; the date shows recency.

```toml
[tool.bumpcalver]
major = 1
minor = 0
patch = 0
version_format = "{major}.{minor}-{current_date}.{build_count}"
date_format = "%Y%m%d"
timezone = "UTC"
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

CLI workflow:
```bash
bumpcalver --build               # → 1.0-20260524.1
bumpcalver --build               # → 1.0-20260524.2  (same day, count increments)
bumpcalver --build --bump minor  # → 1.1-20260524.1  (new feature, minor bumped)
bumpcalver --build --bump major  # → 2.0-20260524.1  (breaking change)
```

> **PEP 440 note:** Add `version_standard = "python"` to convert hyphens to dots for PEP 440: `1.0.20260524.1`. Or use a dot separator in `version_format` from the start: `{major}.{minor}.{current_date}.{build_count}`.

---

### Enterprise Quarterly Release

**Produces:** `26.Q2.01`
**Use case:** A team that ships on a quarterly cadence and wants the quarter explicit in the version string.

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:02}"
date_format = "%y.Q%q"
timezone = "America/New_York"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "RELEASE_VERSION"
file_type = "env"
variable = "VERSION"
version_standard = "default"
```

---

### Hybrid with Full Patch + Padded Build Count

**Produces:** `1.0.0-20260524.001`
**Use case:** A project that wants all three semantic components explicit and a zero-padded three-digit build count for lexicographic sort order.

```toml
[tool.bumpcalver]
major = 1
minor = 0
patch = 0
version_format = "{major}.{minor}.{patch}-{current_date}.{build_count:03}"
date_format = "%Y%m%d"
timezone = "UTC"
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

---

## Pre-release Recipes

### PEP 440 Beta / RC Workflow

**Produces:** `26.05.24.1b1` → `26.05.24.1rc1` → `26.05.24.1`

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count}"
date_format = "%y.%m.%d"
timezone = "UTC"
beta_format    = "b{beta_count}"
rc_format      = "rc{rc_count}"
release_format = ""
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "src/mypackage/__init__.py"
file_type = "python"
variable = "__version__"
version_standard = "python"
```

Typical release cycle:
```bash
bumpcalver --build --beta    # → 26.05.24.1b1  (first beta)
bumpcalver --beta            # → 26.05.24.1b2  (second beta, same build)
bumpcalver --build --rc      # → 26.05.24.2rc1 (promote to rc, new build)
bumpcalver --build           # → 26.05.24.3    (final release, no suffix)
```

**Suffix format reference:**

| Config key | Example output | Notes |
|---|---|---|
| `beta_format = ".beta"` | `26.05.24.1.beta` | Default — omit the key |
| `beta_format = "b{beta_count}"` | `26.05.24.1b1` | PEP 440 style |
| `rc_format = ".rc"` | `26.05.24.1.rc` | Default |
| `rc_format = "rc{rc_count}"` | `26.05.24.1rc1` | PEP 440 style |
| `release_format = ".release"` | `26.05.24.1.release` | Default |
| `release_format = ""` | `26.05.24.1` | No suffix added |

---

## Multi-file / Polyglot Projects

### Full-Stack Web App

Updates Python backend, Node.js frontend, Docker, Make, and Sonar in one command:

```toml
[tool.bumpcalver]
version_format = "{current_date}.{build_count:03}"
date_format = "%y.%m.%d"
timezone = "UTC"
git_tag = true
auto_commit = true

[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "src/backend/__init__.py"
file_type = "python"
variable = "__version__"
version_standard = "python"

[[tool.bumpcalver.file]]
path = "frontend/package.json"
file_type = "json"
variable = "version"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "Dockerfile"
file_type = "dockerfile"
variable = "arg.VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "Makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"

[[tool.bumpcalver.file]]
path = "sonar-project.properties"
file_type = "properties"
variable = "sonar.projectVersion"
version_standard = "default"
```

---

## Standalone `bumpcalver.toml`

If you don't use `pyproject.toml`, create a `bumpcalver.toml` at the project root. Omit the `[tool.bumpcalver]` wrapper and use `[[file]]` instead of `[[tool.bumpcalver.file]]`:

```toml
version_format = "{current_date}.{build_count:03}"
date_format = "%y.%m.%d"
timezone = "America/New_York"
git_tag = true
auto_commit = true
# Pre-release suffix formats (defaults shown — omit keys to use defaults)
# beta_format    = ".beta"
# rc_format      = ".rc"
# release_format = ".release"

[[file]]
path = "Makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"

[[file]]
path = ".env"
file_type = "env"
variable = "VERSION"
version_standard = "default"
```
