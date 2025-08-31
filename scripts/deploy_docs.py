#!/usr/bin/env python3
"""
Documentation deployment script with version management using mike.

This script integrates BumpCalver with mike to automatically deploy versioned documentation.
It reads the current version from various sources and deploys documentation accordingly.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Add the src directory to the path to import bumpcalver modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bumpcalver.handlers import get_version_handler


def get_current_version():
    """Get the current version from multiple sources."""
    version_sources = [
        {"file": "pyproject.toml", "handler": "toml", "variable": "project.version"},
        {"file": "src/bumpcalver/__init__.py", "handler": "python", "variable": "__version__"},
        {"file": "makefile", "handler": "makefile", "variable": "APP_VERSION"},
    ]

    for source in version_sources:
        try:
            handler = get_version_handler(source["handler"])
            version = handler.read_version(source["file"], source["variable"])
            if version:
                print(f"Found version {version} in {source['file']}")
                return version
        except Exception as e:
            print(f"Could not read version from {source['file']}: {e}")
            continue

    # If no version found, check if we're in a GitHub Actions environment
    import os
    github_ref = os.environ.get('GITHUB_REF', '')
    if github_ref.startswith('refs/tags/'):
        version = github_ref.replace('refs/tags/', '').lstrip('v')
        if version:
            print(f"Found version {version} from GitHub tag")
            return version

    return None


def run_command(command, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        raise


def deploy_documentation(version, aliases=None, push=False, title=None, is_dev=False, ignore_remote_status=False):
    """Deploy documentation for a specific version using mike."""
    print(f"Deploying documentation for version: {version}")

    # Validate version format
    if not version or version.strip() == "":
        raise ValueError("Version cannot be empty")

    # Ensure we're in the correct directory
    original_dir = Path.cwd()
    project_root = Path(__file__).parent.parent

    try:
        # Change to project root for mike deployment
        import os
        os.chdir(project_root)

        # Prepare mike command
        cmd = ["mike", "deploy"]

        # Add version
        cmd.append(version)

        # Add aliases if provided
        if aliases:
            cmd.extend(aliases)

        # Add title if provided
        if title:
            cmd.extend(["--title", title])

        # Add update-aliases flag for non-dev versions
        if not is_dev:
            cmd.append("--update-aliases")

        # Add push flag if requested
        if push:
            cmd.append("--push")

        # Handle remote status conflicts
        if ignore_remote_status:
            cmd.extend(["--ignore-remote-status"])

        print(f"Running command: {' '.join(cmd)}")
        print(f"Working directory: {os.getcwd()}")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Documentation deployed successfully!")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error deploying documentation: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        raise
    finally:
        # Always return to original directory
        os.chdir(original_dir)


def list_versions():
    """List all deployed versions."""
    run_command(["mike", "list"])


def serve_docs():
    """Serve documentation locally."""
    run_command(["mike", "serve"])


def delete_version(version, push=False):
    """Delete a specific version."""
    cmd = ["mike", "delete", version]
    if push:
        cmd.append("--push")
    run_command(cmd)


def main():
    """Main function to handle command line arguments and execute appropriate actions."""
    parser = argparse.ArgumentParser(description="Deploy versioned documentation with mike")
    parser.add_argument("action", choices=["deploy", "list", "serve", "delete"],
                       help="Action to perform")
    parser.add_argument("--version", help="Version to deploy (auto-detected if not specified)")
    parser.add_argument("--aliases", nargs="*", default=[],
                       help="Aliases for the version (e.g., latest, stable)")
    parser.add_argument("--push", action="store_true",
                       help="Push to remote repository")
    parser.add_argument("--title", help="Custom title for the version")
    parser.add_argument("--dev", action="store_true",
                       help="Deploy as development version")
    parser.add_argument("--ignore-remote-status", action="store_true",
                       help="Ignore remote git status conflicts")

    args = parser.parse_args()

    try:
        if args.action == "deploy":
            version = args.version
            if not version:
                version = get_current_version()
                if not version:
                    print("Could not determine version automatically. Please specify --version")
                    sys.exit(1)

            # Auto-assign aliases for release versions
            aliases = args.aliases.copy()
            if not args.dev and not aliases:
                # For release versions, automatically add 'latest' alias
                aliases.append("latest")

            deploy_documentation(
                version=version,
                aliases=aliases,
                push=args.push,
                title=args.title,
                is_dev=args.dev,
                ignore_remote_status=args.ignore_remote_status
            )

        elif args.action == "list":
            list_versions()

        elif args.action == "serve":
            serve_docs()

        elif args.action == "delete":
            if not args.version:
                print("Version is required for delete action")
                sys.exit(1)
            delete_version(args.version, args.push)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
