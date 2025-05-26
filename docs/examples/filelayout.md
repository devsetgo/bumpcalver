# Example file layouts
Below are examples of various file types and how they could be setup using BumpCalver. As the intent of the library is to allow flexible use across different languages and use cases.


## MakeFile
```make
# Variables
REPONAME = bumpcalver
APP_VERSION = 2025.02.02
PYTHON = python3
PIP = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest

EXAMPLE_PATH = examples
SERVICE_PATH = src
TESTS_PATH = tests
SQLITE_PATH = _sqlite_db
LOG_PATH = log

PORT = 5000
WORKER = 8
LOG_LEVEL = debug

REQUIREMENTS_PATH = requirements.txt
# DEV_REQUIREMENTS_PATH = requirements/dev.txt

.PHONY: autoflake black cleanup create-docs flake8 help install isort run-example run-example-dev speedtest test

autoflake: ## Remove unused imports and unused variables from Python code
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(SERVICE_PATH)
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(TESTS_PATH)
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports --remove-unused-variables -r $(EXAMPLE_PATH)

```

## YAML

```yaml
application:
  description: This is an example application configuration file.
  name: ExampleApp
configuration:
  version: 2025.02.02
database:
  host: localhost
  password: password
  port: 5432
  username: user
features:
  feature_a: true
  feature_b: false
  feature_c: true
```

## XML
```xml
<configuration>
    <version>2025.02.02</version>
    <application>
        <name>ExampleApp</name>
        <description>This is an example application configuration file.</description>
    </application>
    <database>
        <host>localhost</host>
        <port>5432</port>
        <username>user</username>
        <password>password</password>
    </database>
    <features>
        <feature_a>true</feature_a>
        <feature_b>false</feature_b>
        <feature_c>true</feature_c>
    </features>
</configuration>
```

## TOML
```toml
[configuration]
version = "2025.02.02"

[configuration.application]
name = "ExampleApp"
description = "This is an example application configuration file."

[configuration.database]
host = "localhost"
port = 5432
username = "user"
password = "password"

[configuration.features]
feature_a = true
feature_b = false
feature_c = true

```

## JSON
```json
{
  "version": "2025.02.02",
  "application": {
    "name": "ExampleApp",
    "description": "This is an example application configuration file."
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "username": "user",
    "password": "password"
  },
  "features": {
    "feature_a": true,
    "feature_b": false,
    "feature_c": true
  }
}

```

## Dockerfile
```docker
# Use an official Python runtime as a parent image
FROM python:3.14-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV APP_VERSION=2025.02.02
ARG VERSION=2025.02.02
# Run app.py when the container launches
CMD ["python", "app.py"]

```
