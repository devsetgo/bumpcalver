# =============================================================================
# Project Variables
# =============================================================================
REPONAME = bumpcalver
APP_VERSION = 2025-08-31-003

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
.PHONY: help all autoflake black build bump check-deps clean cleanup create-docs create-docs-dev \
        create-docs-local delete-version dev-setup format install isort list-docs \
        migrate-legacy-docs pre-commit quick-test rebase reinstall ruff serve-docs \
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
autoflake: ## Remove unused imports and unused variables from Python code
	@printf "\033[1;33m🧹 Removing unused imports and variables...\033[0m\n"
	autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --remove-unused-variables -r $(SERVICE_PATH)
	autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --remove-unused-variables -r $(TESTS_PATH)
	autoflake --in-place --remove-all-unused-imports --ignore-init-module-imports --remove-unused-variables -r $(EXAMPLE_PATH)
	@printf "\033[0;32m✅ Autoflake completed!\033[0m\n"

black: ## Reformat Python code to follow the Black code style
	@printf "\033[1;33m🖤 Formatting code with Black...\033[0m\n"
	black $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
	@printf "\033[0;32m✅ Black formatting completed!\033[0m\n"

cleanup: format ## Run all code formatting tools (alias for format)
	@printf "\033[0;32m✅ Code cleanup completed!\033[0m\n"

format: isort ruff autoflake black ## Run all code formatting tools in the correct order
	@printf "\033[0;32m✅ All formatting tools completed!\033[0m\n"

isort: ## Sort imports in Python code
	@printf "\033[1;33m📚 Sorting imports with isort...\033[0m\n"
	isort $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
	@printf "\033[0;32m✅ Import sorting completed!\033[0m\n"

ruff: ## Format Python code with Ruff
	@printf "\033[1;33m🦀 Linting and fixing with Ruff...\033[0m\n"
	ruff check --fix --exit-non-zero-on-fix --show-fixes $(SERVICE_PATH) || true
	ruff check --fix --exit-non-zero-on-fix --show-fixes $(TESTS_PATH) || true
	ruff check --fix --exit-non-zero-on-fix --show-fixes $(EXAMPLE_PATH) || true
	@printf "\033[0;32m✅ Ruff linting completed!\033[0m\n"

validate: ## Validate code without making changes
	@printf "\033[1;33m🔍 Validating code style...\033[0m\n"
	black --check $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
	isort --check-only $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
	ruff check $(SERVICE_PATH) $(TESTS_PATH) $(EXAMPLE_PATH)
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

migrate-legacy-docs: ## Migrate legacy documentation to version 2025.4.12.1 (run once)
	@echo "🚀 Migrating legacy documentation..."
	@python3 scripts/migrate_legacy_docs.py

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
	sed -i 's|<source>.*</source>|<source>$(REPONAME)</source>|' coverage.xml
	genbadge coverage -i coverage.xml
	genbadge tests -i report.xml
	@printf "\033[0;32m✅ All tests passed!\033[0m\n"

test-coverage: ## Run tests and generate coverage report
	@printf "\033[1;33m📊 Generating coverage report...\033[0m\n"
	$(PYTEST) --cov=$(SERVICE_PATH) --cov-report=html --cov-report=term-missing
	@printf "\033[0;32m✅ Coverage report generated in htmlcov/\033[0m\n"

tests: test ## Alias for test target

# =============================================================================
# Commented Out Targets (for reference)
# =============================================================================
# flake8: ## Run flake8 to check Python code for PEP8 compliance
# 	flake8 --tee . > htmlcov/_flake8Report.txt