# File Layout Examples

Below are examples of the version-bearing files BumpCalver can update across different languages and file formats. Each section shows what the file looks like and the `[[tool.bumpcalver.file]]` entry that targets it.

Working copies of every file shown here live in the [`examples/`](https://github.com/devsetgo/bumpcalver/tree/main/examples) directory of the repository. For complete ready-to-run configurations, see the [Configuration Recipes](configuration.md).

---

## Python

### `pyproject.toml`

```toml
[project]
name = "mypackage"
version = "2026.05.24.001"
```

```toml
# bumpcalver config entry
[[tool.bumpcalver.file]]
path = "pyproject.toml"
file_type = "toml"
variable = "project.version"
version_standard = "python"
```

### `__init__.py`

```python
__version__ = "2026.05.24.001"
```

```toml
[[tool.bumpcalver.file]]
path = "src/mypackage/__init__.py"
file_type = "python"
variable = "__version__"
version_standard = "python"
```

### `setup.cfg`

```ini
[metadata]
name = example-package
version = 2026.05.24.001
author = Your Name
author_email = your.email@example.com
description = A short description of the package

[options]
packages = find:
python_requires = >=3.9
install_requires =
    click>=8.0.0
```

```toml
[[tool.bumpcalver.file]]
path = "setup.cfg"
file_type = "setup.cfg"
variable = "metadata.version"
version_standard = "python"
```

---

## Node.js / JavaScript

### `package.json`

```json
{
  "name": "my-app",
  "version": "2026.05.24.1",
  "description": "My application",
  "main": "index.js"
}
```

```toml
[[tool.bumpcalver.file]]
path = "package.json"
file_type = "json"
variable = "version"
version_standard = "default"
```

> The `json` handler updates the **top-level** key. Nested keys are not supported.

---

## Rust

### `Cargo.toml`

```toml
[package]
name = "myapp"
version = "2026.05.24.1"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
```

```toml
[[tool.bumpcalver.file]]
path = "Cargo.toml"
file_type = "toml"
variable = "package.version"
version_standard = "default"
```

---

## Java

### `gradle.properties` (Gradle)

```properties
version=2026.05.24.1
group=com.example
description=My Application
```

```toml
[[tool.bumpcalver.file]]
path = "gradle.properties"
file_type = "properties"
variable = "version"
version_standard = "default"
```

Reference the version in `build.gradle`:
```groovy
version = project.findProperty('version')
```

### `version.properties` (Maven)

```properties
project.version=2026.05.24.1
```

```toml
[[tool.bumpcalver.file]]
path = "version.properties"
file_type = "properties"
variable = "project.version"
version_standard = "default"
```

Load it in `pom.xml` with the Properties Maven Plugin and reference `${project.version}` as usual. See the [Maven recipe](configuration.md#java--maven) for the plugin setup.

---

## Go

### `Makefile` (version passed via `-ldflags`)

```makefile
APP_VERSION = 2026.05.24.001

build:
	go build -ldflags="-X main.Version=$(APP_VERSION)" ./...

.PHONY: build
```

```toml
[[tool.bumpcalver.file]]
path = "Makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"
```

### `version.txt` (embedded via `//go:embed`)

```
VERSION=2026.05.24.001
```

```toml
[[tool.bumpcalver.file]]
path = "version.txt"
file_type = "env"
variable = "VERSION"
version_standard = "default"
```

Go code to read it:
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

## Ruby

### `lib/mygem/version.rb`

```ruby
module MyGem
  VERSION = "2026.05.24.1"
end
```

```toml
[[tool.bumpcalver.file]]
path = "lib/mygem/version.rb"
file_type = "python"
variable = "VERSION"
version_standard = "default"
```

> Ruby constants (`CONSTANT = "value"`) match the same line pattern as Python variables, so `file_type = "python"` works correctly here.

---

## .NET / C#

### `MyApp.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <Version>2026.05.24.1</Version>
    <AssemblyVersion>2026.05.24.1</AssemblyVersion>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
</Project>
```

```toml
[[tool.bumpcalver.file]]
path = "MyApp.csproj"
file_type = "xml"
variable = "PropertyGroup/Version"
version_standard = "default"
```

> The `xml` handler accepts simple XPath paths. `PropertyGroup/Version` finds `<Version>` nested directly inside `<PropertyGroup>` at the document root.

---

## Docker / Containers

### `Dockerfile`

```dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY . /app

ARG VERSION=2026.05.24.1
ENV APP_VERSION=2026.05.24.1

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
CMD ["python", "app.py"]
```

```toml
# Update ARG
[[tool.bumpcalver.file]]
path = "Dockerfile"
file_type = "dockerfile"
variable = "arg.VERSION"
version_standard = "default"

# Update ENV
[[tool.bumpcalver.file]]
path = "Dockerfile"
file_type = "dockerfile"
variable = "env.APP_VERSION"
version_standard = "default"
```

> Prefix `arg.` for `ARG` instructions and `env.` for `ENV` instructions. The same file can appear in multiple entries.

---

## General / Infrastructure

### `Makefile`

```makefile
APP_VERSION = 2026.05.24.001
PYTHON = python3
PIP = $(PYTHON) -m pip

.PHONY: build test

build:
	$(PIP) install -e .

test:
	$(PYTHON) -m pytest
```

```toml
[[tool.bumpcalver.file]]
path = "Makefile"
file_type = "makefile"
variable = "APP_VERSION"
version_standard = "default"
```

### `YAML` config file

```yaml
application:
  name: ExampleApp
  version: "2026.05.24.001"
database:
  host: localhost
  port: 5432
```

```toml
[[tool.bumpcalver.file]]
path = "config.yaml"
file_type = "yaml"
variable = "application.version"
version_standard = "default"
```

### `XML` config file

```xml
<configuration>
    <version>2026.05.24.001</version>
    <application>
        <name>ExampleApp</name>
    </application>
</configuration>
```

```toml
[[tool.bumpcalver.file]]
path = "config.xml"
file_type = "xml"
variable = "version"
version_standard = "default"
```

### Environment file (`.env`)

```env
VERSION=2026.05.24.001
APP_NAME=myapp
DEBUG=false
DATABASE_URL=postgresql://localhost/mydb
```

```toml
[[tool.bumpcalver.file]]
path = ".env"
file_type = "env"
variable = "VERSION"
version_standard = "default"
```

### Properties file (`sonar-project.properties`)

```properties
sonar.projectKey=myorg_myproject
sonar.organization=myorg
sonar.projectName=myproject
sonar.projectVersion=2026.05.24.001
sonar.sources=src
sonar.tests=tests
```

```toml
[[tool.bumpcalver.file]]
path = "sonar-project.properties"
file_type = "properties"
variable = "sonar.projectVersion"
version_standard = "default"
```
