import os
import re
from pathlib import Path

EXAMPLES_DIR = "examples"
DOCS_DIR = "docs/examples"


def extract_metadata(file_path):
    """Extract metadata like docstring and the rest of the code from a Python script."""
    with open(file_path, "r") as f:
        content = f.read()

    # Extract the module-level docstring
    docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    docstring = docstring_match.group(1).strip() if docstring_match else ""

    # Extract everything after the docstring
    if docstring_match:
        code_start = docstring_match.end()
        remaining_code = content[code_start:].strip()
    else:
        remaining_code = content.strip()

    return docstring, remaining_code


def generate_markdown(file_name, docstring, remaining_code):
    """Generate Markdown content for a given example."""
    markdown = f"# {file_name} Example\n\n"
    if docstring:
        markdown += f"{docstring}\n\n"
    markdown += "```python\n"
    markdown += remaining_code
    markdown += "\n```\n"
    return markdown


def get_language_from_extension(file_path: Path) -> str:
    """Return a code fence language based on file extension."""
    ext = file_path.suffix.lower()
    if ext == ".py":
        return "python"
    elif ext in [".yml", ".yaml"]:
        return "yaml"
    elif ext == ".xml":
        return "xml"
    elif ext == ".json":
        return "json"
    elif ext == ".toml":
        return "toml"
    elif ext == ".make" or file_path.name == "makefile":
        return "make"
    elif file_path.name.endswith("dockerfile"):
        return "docker"
    return ""


def update_docs():
    """Scan examples and update documentation, excluding mkdocs.yml operations."""
    examples_path = Path(EXAMPLES_DIR)
    docs_path = Path(DOCS_DIR)

    # Ensure the docs directory exists
    docs_path.mkdir(parents=True, exist_ok=True)

    # Scan examples folder
    example_files = examples_path.glob("*.*")  # Scan all files

    for example_file in example_files:
        if example_file.name == "__init__.py":
            continue

        file_name = example_file.stem
        docstring, full_code = extract_metadata(example_file)

        # Determine code fence language
        fence_lang = get_language_from_extension(example_file)

        # Decide which markdown file to update
        if example_file.name == "pyproject.toml" or example_file.name == "bumpcalver.toml":
            # Update configuration.md (pyproject first, then bumpcalver)
            # Logic to update configuration.md
            # Insert pyproject.toml section first, then bumpcalver.toml
            continue
        else:
            # Update filelayout.md
            # Logic to update filelayout.md
            # Create a new section if we find a new type
            continue

        # Generate Markdown content
        markdown_content = generate_markdown(file_name, docstring, full_code)

        # Write to Markdown file
        markdown_file = docs_path / f"{file_name}.md"
        with open(markdown_file, "w") as f:
            f.write(markdown_content)


if __name__ == "__main__":
    update_docs()
