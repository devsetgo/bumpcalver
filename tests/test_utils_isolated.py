"""
Test utilities for creating isolated test environments.

This module provides utilities for creating temporary test files and configurations
that can be used to test file update functionality without affecting real project files.
"""

import os
import tempfile
import shutil
from contextlib import contextmanager


@contextmanager
def isolated_test_environment():
    """
    Create a temporary directory for isolated testing.
    
    Yields the path to the temporary directory. The directory and all its contents
    are automatically cleaned up when the context exits.
    
    Example:
        with isolated_test_environment() as temp_dir:
            test_file = os.path.join(temp_dir, "test.py")
            # Create and use test files...
    """
    temp_dir = tempfile.mkdtemp(prefix="bumpcalver_test_")
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_test_file(directory: str, filename: str, content: str) -> str:
    """
    Create a test file with the given content.
    
    Args:
        directory: Directory where the file should be created
        filename: Name of the file to create
        content: Content to write to the file
        
    Returns:
        Full path to the created file
    """
    file_path = os.path.join(directory, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path


def create_sample_python_file(temp_dir: str, version: str = "0.1.0") -> str:
    """
    Create a sample Python file with a version variable.
    
    Args:
        temp_dir: Directory where the file should be created
        version: Initial version to set
        
    Returns:
        Full path to the created file
    """
    content = f'__version__ = "{version}"\n\ndef hello():\n    return "Hello, World!"\n'
    return create_test_file(temp_dir, "test_module.py", content)


def verify_python_version(file_path: str, expected_version: str) -> bool:
    """
    Verify that a Python file contains the expected version.
    
    Args:
        file_path: Path to the Python file to check
        expected_version: The version that should be in the file
        
    Returns:
        True if the file contains the expected version, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return f'__version__ = "{expected_version}"' in content
