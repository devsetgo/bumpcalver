# Documentation Versioning with Mike

This project uses [mike](https://github.com/jimporter/mike) to manage multiple versions of the documentation. Mike integrates with MkDocs to provide a smooth versioning experience.

## Overview

The documentation versioning system allows you to:
- Deploy multiple versions of documentation simultaneously
- Automatically manage version aliases (latest, stable, dev)
- Provide a version selector in the documentation
- Maintain clean URLs for different versions

## Version Strategy

### Version Formats
- **Release versions**: Use calendar versioning format (e.g., `2025.08.01`)
- **Development version**: `dev`
- **Aliases**: `latest`, `stable`

### Version Hierarchy
1. `latest` - Always points to the most recent release
2. `stable` - Points to the current stable release
3. `dev` - Development/bleeding-edge documentation
4. Specific versions (e.g., `2025.08.01`, `2025.07.15`)

## Commands

### Deployment Commands

```bash
# Deploy current version (auto-detected from project files)
make create-docs

# Deploy locally without pushing to remote
make create-docs-local

# Deploy development version
make create-docs-dev

# Deploy specific version with custom aliases
python3 scripts/deploy_docs.py deploy --version 2025.08.01 --aliases latest stable --push

# Deploy development version
python3 scripts/deploy_docs.py deploy --dev --version dev --push
```

### Management Commands

```bash
# List all deployed versions
make list-docs
# or
python3 scripts/deploy_docs.py list

# Serve all versions locally for testing
make serve-docs
# or
python3 scripts/deploy_docs.py serve

# Delete a specific version
make delete-version VERSION=2025.07.01
# or
python3 scripts/deploy_docs.py delete --version 2025.07.01 --push

# Set default version (what users see at the root URL)
make set-default-version VERSION=latest
```

## Workflow Integration

### Automated Deployment

The project includes GitHub Actions workflows that automatically deploy documentation:

1. **Push to `dev` branch**: Deploys to `dev` version
2. **Push to `main`/`master` branch**: Deploys as new release with `latest` alias
3. **Tagged releases**: Deploys with both `latest` and `stable` aliases

### Manual Deployment

For manual deployment, follow these steps:

1. **Update version**: Use bumpcalver to update project version
   ```bash
   bumpcalver --build
   ```

2. **Deploy documentation**:
   ```bash
   make create-docs
   ```

## Configuration

### MkDocs Configuration

The `mkdocs.yml` file includes the mike plugin configuration:

```yaml
plugins:
  - mike:
      alias_type: symlink
      version_selector: true
      css_dir: css
      javascript_dir: js
```

### Mike Configuration

Project-specific mike settings are stored in `.mike.yml`:

```yaml
remote_branch: gh-pages
remote_name: origin
version_selector: true
default_alias_type: symlink
```

## Version Selector

The documentation includes an automatic version selector that:
- Appears in the navigation bar
- Shows all available versions
- Allows users to switch between versions
- Highlights the current version

## Best Practices

### Version Management
1. **Always use aliases**: Use `latest` and `stable` aliases for user-friendly URLs
2. **Regular cleanup**: Remove old versions that are no longer supported
3. **Consistent naming**: Follow the established version naming convention
4. **Test locally**: Use `make serve-docs` to test before deploying

### Release Process
1. **Development**: Work on `dev` branch, deploy to `dev` version
2. **Review**: Test documentation thoroughly using local serving
3. **Release**: Merge to main, automatic deployment creates new versioned docs
4. **Tag**: Create Git tags for major releases to create permanent documentation snapshots

### URL Structure

The documentation will be available at:
- `https://yoursite.com/` - Default version (usually `latest`)
- `https://yoursite.com/latest/` - Latest release
- `https://yoursite.com/stable/` - Stable release
- `https://yoursite.com/dev/` - Development version
- `https://yoursite.com/2025.08.01/` - Specific version

## Troubleshooting

### Common Issues

1. **Version not found**: Ensure the version exists with `make list-docs`
2. **Git permissions**: Configure Git user for automated deployments
3. **Branch conflicts**: Fetch latest changes before deploying

### Recovery

If something goes wrong:

```bash
# List all versions to see current state
make list-docs

# Delete problematic version
make delete-version VERSION=problematic-version

# Redeploy from scratch
make create-docs-local
```

## Integration with BumpCalver

The versioning system integrates seamlessly with BumpCalver:

1. **Version detection**: Automatically reads version from project files
2. **Consistent versioning**: Uses the same version format across project and docs
3. **Automated workflow**: Version bumps trigger documentation updates

This ensures that documentation versions always match the project versions.
