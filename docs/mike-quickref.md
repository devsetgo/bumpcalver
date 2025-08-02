# Mike Documentation Versioning - Quick Reference

## Quick Commands

### Deploy Documentation
```bash
# Deploy current version (auto-detected)
make create-docs                 # Push to remote
make create-docs-local          # Local only

# Deploy development version
make create-docs-dev            # Push dev version

# Deploy specific version
python3 scripts/deploy_docs.py deploy --version 2025.08.01 --aliases latest stable --push
```

### Manage Versions
```bash
# List all versions
make list-docs

# Serve locally (all versions)
make serve-docs

# Delete version
make delete-version VERSION=2025.07.01

# Set default version
make set-default-version VERSION=latest
```

### Advanced Usage
```bash
# Deploy with custom title
python3 scripts/deploy_docs.py deploy --version 2025.08.01 --title "August 2025 Release" --push

# Deploy dev version with custom name
python3 scripts/deploy_docs.py deploy --dev --version staging --push

# Deploy without aliases
python3 scripts/deploy_docs.py deploy --version 2025.08.01 --push
```

## Version Strategy

| Version Type | Format | Example | When to Use |
|-------------|--------|---------|-------------|
| Release | YYYY.MM.DD | 2025.08.01 | Tagged releases |
| Development | dev | dev | Active development |
| Staging | staging | staging | Pre-release testing |
| Aliases | latest/stable | latest | User-friendly URLs |

## URL Structure

| URL | Points To | Description |
|-----|-----------|-------------|
| `/` | Default version | Usually `latest` |
| `/latest/` | Latest release | Most recent version |
| `/stable/` | Stable release | Production-ready |
| `/dev/` | Development | Bleeding edge |
| `/2025.08.01/` | Specific version | Permanent link |

## Integration Points

### With BumpCalver
- Auto-detects version from `makefile`, `pyproject.toml`, `__init__.py`
- Consistent versioning across project and docs
- Automated workflow on version bumps

### With GitHub Actions
- `dev` branch → `dev` documentation
- `main` branch → `latest` documentation
- Git tags → versioned + `stable` documentation

### With MkDocs Material Theme
- Automatic version selector in navigation
- Responsive design across versions
- Search within specific versions
