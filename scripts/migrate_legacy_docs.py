#!/usr/bin/env python3
"""
Migration script to preserve existing documentation as version 2025.4.12.1
and clean up mixed legacy content from gh-pages branch.
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def run_command(cmd, description, check=True):
    """Run a shell command with error handling."""
    print(f"→ {description}")
    print(f"  Running: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if check and result.returncode != 0:
        print(f"  ❌ Error: {result.stderr}")
        sys.exit(1)

    if result.stdout:
        print(f"  Output: {result.stdout.strip()}")

    return result

def backup_existing_mike_versions():
    """Backup existing mike-managed versions."""
    print("\n📦 Backing up existing mike versions...")

    # Switch to gh-pages to examine current state
    run_command("git checkout gh-pages", "Switching to gh-pages branch")

    # Check if versions.json exists
    if os.path.exists("versions.json"):
        with open("versions.json", 'r') as f:
            existing_versions = json.load(f)
        print(f"  Found existing versions: {[v['version'] for v in existing_versions]}")
        return existing_versions
    else:
        print("  No existing versions.json found")
        return []

def identify_legacy_content():
    """Identify content that's not part of mike's version directories."""
    print("\n🔍 Identifying legacy content...")

    # Mike-managed directories and files
    mike_items = {
        "2025.07.01", "2025.08.01", "dev", "latest",  # Version directories and symlinks
        "versions.json", "index.html", ".nojekyll"     # Mike management files
    }

    # Get all items in gh-pages root
    all_items = set(os.listdir("."))

    # Remove git and development artifacts
    ignore_items = {
        ".git", ".coverage", ".pytest_cache", ".ruff_cache",
        "_venv", "dist", "htmlcov", "src", "tests", "site"
    }

    # Legacy content = all items - mike items - ignore items
    legacy_items = all_items - mike_items - ignore_items

    print(f"  Mike-managed: {sorted(mike_items & all_items)}")
    print(f"  Legacy content: {sorted(legacy_items)}")
    print(f"  Ignored items: {sorted(ignore_items & all_items)}")

    return legacy_items

def create_legacy_version(legacy_items, target_version="2025.4.12.1"):
    """Create a version directory for legacy documentation."""
    print(f"\n📚 Creating version {target_version} from legacy content...")

    # Create version directory
    version_dir = Path(target_version)
    if version_dir.exists():
        print(f"  Directory {target_version} already exists, removing...")
        shutil.rmtree(version_dir)

    version_dir.mkdir()

    # Copy legacy items into version directory
    for item in legacy_items:
        src_path = Path(item)
        dst_path = version_dir / item

        if src_path.is_dir():
            shutil.copytree(src_path, dst_path)
            print(f"  📁 Copied directory: {item}")
        else:
            shutil.copy2(src_path, dst_path)
            print(f"  📄 Copied file: {item}")

    # Ensure the main index.html points to something reasonable
    main_index = version_dir / "index.html"
    if not main_index.exists():
        # Create a basic index if one doesn't exist
        with open(main_index, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>BumpCalVer Documentation</title>
    <meta http-equiv="refresh" content="0; url=./quickstart/">
</head>
<body>
    <p>Redirecting to documentation...</p>
</body>
</html>
""")
        print(f"  📄 Created basic index.html")

    return version_dir

def update_versions_json(target_version="2025.4.12.1"):
    """Update versions.json to include the legacy version."""
    print(f"\n📝 Updating versions.json...")

    # Load existing versions
    versions = []
    if os.path.exists("versions.json"):
        with open("versions.json", 'r') as f:
            versions = json.load(f)

    # Check if target version already exists
    existing_version = next((v for v in versions if v['version'] == target_version), None)

    if not existing_version:
        # Add the legacy version
        legacy_version = {
            "version": target_version,
            "title": f"Release {target_version}",
            "aliases": []
        }

        # Insert at the beginning (oldest version first)
        versions.insert(0, legacy_version)
        print(f"  ✅ Added version {target_version}")
    else:
        print(f"  ℹ️  Version {target_version} already exists")

    # Write back to versions.json
    with open("versions.json", 'w') as f:
        json.dump(versions, f, indent=2)

    print(f"  📊 Current versions: {[v['version'] for v in versions]}")

def clean_legacy_content(legacy_items):
    """Remove legacy content from gh-pages root."""
    print(f"\n🧹 Cleaning legacy content from root...")

    for item in legacy_items:
        item_path = Path(item)
        try:
            if item_path.is_dir():
                shutil.rmtree(item_path)
                print(f"  🗂️  Removed directory: {item}")
            else:
                item_path.unlink()
                print(f"  📄 Removed file: {item}")
        except Exception as e:
            print(f"  ⚠️  Could not remove {item}: {e}")

def commit_changes(target_version="2025.4.12.1"):
    """Commit the migration changes."""
    print(f"\n💾 Committing migration changes...")

    # Configure git user
    run_command('git config user.name "Documentation Migration"', "Setting git user")
    run_command('git config user.email "migration@bumpcalver.local"', "Setting git email")

    # Add all changes
    run_command("git add .", "Adding all changes")

    # Commit
    commit_msg = f"Migrate legacy documentation to version {target_version}"
    run_command(f'git commit -m "{commit_msg}"', "Committing changes")

def main():
    """Main migration process."""
    print("🚀 Starting documentation migration...")
    print("=" * 60)

    target_version = "2025.4.12.1"

    # Backup and analyze current state
    existing_versions = backup_existing_mike_versions()
    legacy_items = identify_legacy_content()

    if not legacy_items:
        print("\n✅ No legacy content found. Documentation is already properly organized!")
        return

    print(f"\n📋 Migration Plan:")
    print(f"  • Create version: {target_version}")
    print(f"  • Migrate {len(legacy_items)} legacy items")
    print(f"  • Clean up root directory")
    print(f"  • Update versions.json")

    # Ask for confirmation
    response = input("\nProceed with migration? (y/N): ").strip().lower()
    if response != 'y':
        print("Migration cancelled.")
        return

    # Perform migration
    try:
        create_legacy_version(legacy_items, target_version)
        update_versions_json(target_version)
        clean_legacy_content(legacy_items)
        commit_changes(target_version)

        print("\n🎉 Migration completed successfully!")
        print(f"✅ Legacy documentation preserved as version {target_version}")
        print("✅ Root directory cleaned up")
        print("✅ versions.json updated")
        print("\nNext steps:")
        print("1. Push changes: git push origin gh-pages")
        print("2. Test documentation: https://devsetgo.github.io/bumpcalver/")
        print("3. Deploy new version when ready")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("You may need to manually review and fix the gh-pages branch.")
        sys.exit(1)

if __name__ == "__main__":
    main()
