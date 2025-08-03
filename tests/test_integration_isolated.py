"""
Example of how to safely test file update functionality without affecting real project files.

This test demonstrates the proper way to test handlers in isolation using temporary files.
"""

import pytest
from tests.test_utils_isolated import (
    isolated_test_environment,
    create_sample_python_file,
    verify_python_version
)
from src.bumpcalver.handlers import get_version_handler


class TestHandlerIsolated:
    """Example tests that demonstrate safe testing with isolated environments."""
    
    def test_python_handler_update(self):
        """Test updating a Python file in an isolated environment."""
        with isolated_test_environment() as temp_dir:
            # Create a sample Python file
            python_file = create_sample_python_file(temp_dir, "0.1.0")
            
            # Get the Python handler
            handler = get_version_handler("python")
            
            # Test version to update to
            test_version = "2025-01-15-001"
            
            # Update the file
            success = handler.update_version(
                file_path=python_file,
                variable="__version__",
                new_version=test_version
            )
            
            assert success, "Failed to update Python file"
            assert verify_python_version(python_file, test_version), \
                f"Version {test_version} not found in updated file"
    
    def test_python_handler_rollback(self):
        """Test rollback functionality in an isolated environment."""
        with isolated_test_environment() as temp_dir:
            # Create a sample Python file
            python_file = create_sample_python_file(temp_dir, "0.1.0")
            original_version = "0.1.0"
            
            # Get the Python handler
            handler = get_version_handler("python")
            
            # First update
            success = handler.update_version(
                file_path=python_file,
                variable="__version__",
                new_version="2025-01-15-001"
            )
            
            assert success
            assert verify_python_version(python_file, "2025-01-15-001")
            
            # Rollback to original version
            success = handler.update_version(
                file_path=python_file,
                variable="__version__",
                new_version=original_version
            )
            
            assert success
            assert verify_python_version(python_file, original_version)
    
    def test_nonexistent_file_handling(self):
        """Test error handling with non-existent files."""
        with isolated_test_environment() as temp_dir:
            # Try to update a non-existent file
            handler = get_version_handler("python")
            
            non_existent_file = f"{temp_dir}/does_not_exist.py"
            
            success = handler.update_version(
                file_path=non_existent_file,
                variable="__version__",
                new_version="2025-01-15-001"
            )
            
            # Should fail gracefully
            assert not success
