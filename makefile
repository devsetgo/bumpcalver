# =============================================================================
# Project Variables
# =============================================================================
REPONAME = bumpcalver
APP_VERSION = 2026.05.24.001

# Python Configuration
PYTHON = python3
PIP = $(PYTHON) -m pip
PYTEST = $(PYTHON) -m pytest

# Path Configuration
EXAMPLE_PATH = examples
SERVICE_PATH = src
TESTS_PATH = tests
SQLITE_PATH = _sqlite_db
LOG_PATH = log

# Server Configuration (if needed)
PORT = 5000
WORKER = 8
LOG_LEVEL = debug

# Requirements
REQUIREMENTS_PATH = requirements.txt
# DEV_REQUIREMENTS_PATH = requirements/dev.txt

# =============================================================================
# Safety Checks
# =============================================================================
# Make will use bash instead of sh
SHELL := /bin/bash

# Make will exit on errors
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

# Delete target files if the command fails
.DELETE_ON_ERROR:

# Warn if variables are undefined
MAKEFLAGS += --warn-undefined-variables

# Disable built-in implicit rules
.SUFFIXES:

# =============================================================================
# Phony Targets
# =============================================================================
.PHONY: help all build bump check-deps clean cleanup create-docs create-docs-dev \
        create-docs-local delete-version dev-setup format install list-docs \
        mypy pre-commit quick-test rebase reinstall ruff serve-docs \
        set-default-version sync-docs-branch test test-coverage tests validate

# =============================================================================
# Default Target
# =============================================================================
.DEFAULT_GOAL := help

# =============================================================================
# Help Target
# =============================================================================
help:  ## Display this help message
	@echo ""
	@printf "\033[0;36m████████████████████████████████████████████████████████████████\033[0m\n"
	@printf "\033[0;36m█                    \033[1;37m$(REPONAME) Makefile\033[0;36m                     █\033[0m\n"
	@printf "\033[0;36m████████████████████████████████████████████████████████████████\033[0m\n"
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1;37mUsage:\033[0m\n  make \033[0;36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[0;36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1;33m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Quick Start
all: install format test build ## Run the complete development workflow
	@printf "\033[0;32m✅ Complete workflow finished successfully!\033[0m\n"

dev-setup: install pre-commit ## Set up development environment
	@printf "\033[0;32m✅ Development environment set up successfully!\033[0m\n"

quick-test: format ## Run quick tests (no pre-commit hooks)
	@printf "\033[1;33m🧪 Running quick tests...\033[0m\n"
	$(PYTEST)
	@printf "\033[0;32m✅ Quick tests passed!\033[0m\n"

##@ Build and Version Management
build: ## Build the project
	@printf "\033[1;33m📦 Building project...\033[0m\n"
	$(PYTHON) -m build
	@printf "\033[0;32m✅ Build completed successfully!\033[0m\n"

bump: ## Bump calver version
	@printf "\033[1;33m📈 Bumping version...\033[0m\n"
	bumpcalver --build
	@printf "\033[0;32m✅ Version bumped successfully!\033[0m\n"

##@ Code Formatting and Linting
# Ruff is the single tool for linting, import sorting, unused-import/variable
# removal, and formatting (its `format` subcommand is a Black-compatible
# formatter) — see IMPROVEMENTS.md §2.9 for why the isort/black/autoflake/
# flake8/autopep8 targets that used to live here were retired in favor of it.
cleanup: format ## Run all code formatting tools (alias for format)
	@printf "\033[0;32m✅ Code cleanup completed!\033[0m\n"

format: ## Fix lint issues (incl. import sorting) and reformat code with Ruff
	@printf "\033[1;33m🦀 Fixing and formatting with Ruff...\033[0m\n"
	ruff check --fix --exit-non-zero-on-fix --show-fixes $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH) || true
	ruff format $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
	@printf "\033[0;32m✅ Formatting completed!\033[0m\n"

mypy: ## Type-check src/bumpcalver with mypy
	@printf "\033[1;33m🔎 Type-checking with mypy...\033[0m\n"
	mypy
	@printf "\033[0;32m✅ Type checking completed!\033[0m\n"

ruff: format ## Alias for format (kept for muscle memory / older docs)

validate: ## Validate code style and types without making changes
	@printf "\033[1;33m🔍 Validating code style...\033[0m\n"
	ruff format --check $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
	ruff check $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
	mypy
	@printf "\033[0;32m✅ Code validation passed!\033[0m\n"

##@ Documentation Management
create-docs: sync-docs-branch ## Build and deploy the project's documentation with versioning
	python3 scripts/update_docs.py
	python3 scripts/changelog.py
	cp /workspaces/$(REPONAME)/README.md /workspaces/$(REPONAME)/docs/index.md
	cp /workspaces/$(REPONAME)/CONTRIBUTING.md /workspaces/$(REPONAME)/docs/contribute.md
	cp /workspaces/$(REPONAME)/CHANGELOG.md /workspaces/$(REPONAME)/docs/release-notes.md
	python3 scripts/deploy_docs.py deploy --push --ignore-remote-status

create-docs-dev: sync-docs-branch ## Build and deploy a development version of the documentation
	python3 scripts/update_docs.py
	python3 scripts/changelog.py
	cp /workspaces/$(REPONAME)/README.md /workspaces/$(REPONAME)/docs/index.md
	cp /workspaces/$(REPONAME)/CONTRIBUTING.md /workspaces/$(REPONAME)/docs/contribute.md
	cp /workspaces/$(REPONAME)/CHANGELOG.md /workspaces/$(REPONAME)/docs/release-notes.md
	python3 scripts/deploy_docs.py deploy --dev --version dev --push --ignore-remote-status

create-docs-local: ## Build and deploy the project's documentation locally with versioning
	python3 scripts/update_docs.py
	python3 scripts/changelog.py
	cp /workspaces/$(REPONAME)/README.md /workspaces/$(REPONAME)/docs/index.md
	cp /workspaces/$(REPONAME)/CONTRIBUTING.md /workspaces/$(REPONAME)/docs/contribute.md
	cp /workspaces/$(REPONAME)/CHANGELOG.md /workspaces/$(REPONAME)/docs/release-notes.md
	python3 scripts/deploy_docs.py deploy

delete-version: ## Delete a specific documentation version (requires VERSION parameter)
	python3 scripts/deploy_docs.py delete --version $(VERSION)

list-docs: ## List all deployed documentation versions
	python3 scripts/deploy_docs.py list

serve-docs: ## Serve all documentation versions locally
	python3 scripts/deploy_docs.py serve

set-default-version: ## Set the default version for documentation (requires VERSION parameter)
	mike set-default $(VERSION)

sync-docs-branch: ## Sync local gh-pages with remote before deployment
	@echo "🔄 Syncing gh-pages branch..."
	@git fetch origin gh-pages
	@git checkout gh-pages 2>/dev/null || echo "gh-pages branch exists"
	@git reset --hard origin/gh-pages
	@git checkout dev

##@ Git Operations
rebase: ## Rebase the current branch onto the main branch
	@printf "\033[1;33m🔄 Rebasing onto main...\033[0m\n"
	git fetch origin main
	git rebase origin/main
	@printf "\033[0;32m✅ Rebase completed!\033[0m\n"

##@ Maintenance and Cleanup
check-deps: ## Check for outdated dependencies
	@printf "\033[1;33m🔍 Checking for outdated dependencies...\033[0m\n"
	$(PIP) list --outdated
	@printf "\033[0;32m✅ Dependency check completed!\033[0m\n"

clean: ## Clean up generated files and caches
	@printf "\033[1;33m🧹 Cleaning up...\033[0m\n"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .ruff_cache/ 2>/dev/null || true
	@printf "\033[0;32m✅ Cleanup completed!\033[0m\n"

##@ Setup and Installation
install: ## Install the project's dependencies
	@printf "\033[1;33m📦 Installing dependencies...\033[0m\n"
	$(PIP) install -r $(REQUIREMENTS_PATH)
	$(PIP) install -e .
	@printf "\033[0;32m✅ Dependencies installed successfully!\033[0m\n"

pre-commit: ## Set up pre-commit hooks
	@printf "\033[1;33m🔗 Setting up pre-commit hooks...\033[0m\n"
	pre-commit install
	@printf "\033[0;32m✅ Pre-commit hooks installed!\033[0m\n"

reinstall: clean ## Clean and reinstall the project's dependencies
	@printf "\033[1;33m♻️  Reinstalling dependencies...\033[0m\n"
	$(PIP) uninstall -r $(REQUIREMENTS_PATH) -y
	$(PIP) install -r $(REQUIREMENTS_PATH)
	@printf "\033[0;32m✅ Dependencies reinstalled successfully!\033[0m\n"

##@ Testing and Quality Assurance
test: ## Run the project's tests with pre-commit hooks
	@printf "\033[1;33m🧪 Running full test suite...\033[0m\n"
	pre-commit run -a
	$(PYTEST) --cov=$(SERVICE_PATH) --cov-report=xml --cov-report=html --junitxml=report.xml
	$(PYTHON) -c 'import re; from pathlib import Path; p=Path("coverage.xml"); t=p.read_text(encoding="utf-8"); new="<sources>\\n\\t\\t<source>src</source>\\n\\t</sources>"; t=re.sub(r"(?s)<sources>.*?</sources>", new, t, count=1); p.write_text(t, encoding="utf-8")'
	genbadge coverage -i coverage.xml
	genbadge tests -i report.xml
	@printf "\033[0;32m✅ All tests passed!\033[0m\n"

test-coverage: ## Run tests and generate coverage report
	@printf "\033[1;33m📊 Generating coverage report...\033[0m\n"
	$(PYTEST) --cov=$(SERVICE_PATH) --cov-report=html --cov-report=term-missing
	@printf "\033[0;32m✅ Coverage report generated in htmlcov/\033[0m\n"

tests: test ## Alias for test target
