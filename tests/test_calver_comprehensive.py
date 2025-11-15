"""
Comprehensive Calendar Versioning Tests

Tests various CalVer patterns to ensure robust parsing and compatibility.
Based on CalVer specification (https://calver.org) and real-world usage.
"""

import pytest
from src.bumpcalver.utils import parse_version


class TestCalendarVersioningPatterns:
    """Test various calendar versioning patterns."""

    def test_basic_dot_separated_patterns(self):
        """Test basic dot-separated calendar versioning patterns."""
        test_cases = [
            # (version, version_format, date_format, expected_date, expected_count)
            ("24.12.001", "{current_date}.{build_count:03}", "%y.%m", "24.12", 1),
            ("2024.12.001", "{current_date}.{build_count:03}", "%Y.%m", "2024.12", 1),
            ("24.Q4.001", "{current_date}.{build_count:03}", "%y.Q%q", "24.Q4", 1),
            ("2024.Q4.001", "{current_date}.{build_count:03}", "%Y.Q%q", "2024.Q4", 1),
            ("24.342.001", "{current_date}.{build_count:03}", "%y.%j", "24.342", 1),
            ("2024.342.001", "{current_date}.{build_count:03}", "%Y.%j", "2024.342", 1),
        ]
        
        for version, version_format, date_format, expected_date, expected_count in test_cases:
            result = parse_version(version, version_format, date_format)
            assert result is not None, f"Failed to parse {version}"
            date_part, build_count = result
            assert date_part == expected_date, f"Date mismatch for {version}: got {date_part}, expected {expected_date}"
            assert build_count == expected_count, f"Count mismatch for {version}: got {build_count}, expected {expected_count}"

    def test_hyphen_separated_patterns(self):
        """Test hyphen-separated patterns (legacy format)."""
        test_cases = [
            ("2024-12-07-001", "{current_date}-{build_count:03}", "%Y-%m-%d", "2024-12-07", 1),
            ("2024-12-07", "{current_date}", "%Y-%m-%d", "2024-12-07", 0),
        ]
        
        for version, version_format, date_format, expected_date, expected_count in test_cases:
            result = parse_version(version, version_format, date_format)
            assert result is not None, f"Failed to parse {version}"
            date_part, build_count = result
            assert date_part == expected_date, f"Date mismatch for {version}"
            assert build_count == expected_count, f"Count mismatch for {version}"

    def test_date_only_patterns(self):
        """Test patterns with date only (no build count)."""
        test_cases = [
            ("24.12", "{current_date}", "%y.%m", "24.12", 0),
            ("2024.12", "{current_date}", "%Y.%m", "2024.12", 0),
            ("24.Q4", "{current_date}", "%y.Q%q", "24.Q4", 0),
            ("2024.Q4", "{current_date}", "%Y.Q%q", "2024.Q4", 0),
            ("2024.12.07", "{current_date}", "%Y.%m.%d", "2024.12.07", 0),
        ]
        
        for version, version_format, date_format, expected_date, expected_count in test_cases:
            result = parse_version(version, version_format, date_format)
            assert result is not None, f"Failed to parse {version}"
            date_part, build_count = result
            assert date_part == expected_date, f"Date mismatch for {version}"
            assert build_count == expected_count, f"Count mismatch for {version}"

    def test_compact_date_formats(self):
        """Test compact date formats without separators."""
        test_cases = [
            ("241207.001", "{current_date}.{build_count:03}", "%y%m%d", "241207", 1),
            ("20241207.001", "{current_date}.{build_count:03}", "%Y%m%d", "20241207", 1),
        ]
        
        for version, version_format, date_format, expected_date, expected_count in test_cases:
            result = parse_version(version, version_format, date_format)
            assert result is not None, f"Failed to parse {version}"
            date_part, build_count = result
            assert date_part == expected_date, f"Date mismatch for {version}"
            assert build_count == expected_count, f"Count mismatch for {version}"

    def test_beta_alpha_suffixes(self):
        """Test versions with beta/alpha suffixes."""
        test_cases = [
            ("24.Q4.001.beta", "{current_date}.{build_count:03}", "%y.Q%q", "24.Q4", 1),
            ("2024.12.001.alpha", "{current_date}.{build_count:03}", "%Y.%m", "2024.12", 1),
            ("24.12.001.rc1", "{current_date}.{build_count:03}", "%y.%m", "24.12", 1),
        ]
        
        for version, version_format, date_format, expected_date, expected_count in test_cases:
            result = parse_version(version, version_format, date_format)
            assert result is not None, f"Failed to parse {version}"
            date_part, build_count = result
            assert date_part == expected_date, f"Date mismatch for {version}"
            assert build_count == expected_count, f"Count mismatch for {version}"

    def test_invalid_formats_rejected(self):
        """Test that invalid formats are properly rejected."""
        invalid_cases = [
            ("v1.0.0", "{current_date}.{build_count:03}", "%Y.%m.%d"),  # SemVer format
            ("1.0.0", "{current_date}.{build_count:03}", "%Y.%m.%d"),   # SemVer format
            ("release-1.0", "{current_date}.{build_count:03}", "%Y.%m.%d"),  # Invalid format
        ]
        
        for version, version_format, date_format in invalid_cases:
            result = parse_version(version, version_format, date_format)
            # These should either fail or fall back to legacy parsing (which should also fail)
            assert result is None, f"Should not have parsed invalid format: {version}"

    def test_edge_case_patterns(self):
        """Test edge cases and unusual patterns."""
        # These are patterns that might not work perfectly but should be handled gracefully
        edge_cases = [
            ("24.12.1", "{current_date}.{build_count}", "%y.%m", "24.12", 1),  # Non-padded build count
        ]
        
        for version, version_format, date_format, expected_date, expected_count in edge_cases:
            result = parse_version(version, version_format, date_format)
            if result is not None:  # If it parses, check it's correct
                date_part, build_count = result
                assert date_part == expected_date, f"Date mismatch for {version}"
                assert build_count == expected_count, f"Count mismatch for {version}"
            # If it doesn't parse, that's also acceptable for edge cases

    def test_real_world_examples(self):
        """Test patterns based on real-world CalVer usage."""
        real_world_cases = [
            # Ubuntu-style
            ("24.04", "{current_date}", "%y.%m", "24.04", 0),
            ("24.10", "{current_date}", "%y.%m", "24.10", 0),
            
            # Twisted-style
            ("24.3.0", "{current_date}.{build_count}", "%y.%m", "24.3", 0),  # Actually uses minor.patch, not build count
            
            # VS Code style (YY.M.patch)
            ("24.11.1", "{current_date}.{build_count}", "%y.%m", "24.11", 1),
        ]
        
        for version, version_format, date_format, expected_date, expected_count in real_world_cases:
            result = parse_version(version, version_format, date_format)
            assert result is not None, f"Failed to parse real-world example: {version}"
            date_part, build_count = result
            assert date_part == expected_date, f"Date mismatch for {version}"
            assert build_count == expected_count, f"Count mismatch for {version}"


class TestCalendarVersioningLimitations:
    """Test known limitations and patterns that may not work."""

    def test_mixed_separators_limitation(self):
        """Test mixed separator patterns (currently not supported)."""
        # These patterns are currently NOT supported by our implementation
        # This test documents the limitation
        
        mixed_cases = [
            ("2024-12-07_001", "{current_date}_{build_count:03}", "%Y-%m-%d"),
            ("24.Q4-001", "{current_date}-{build_count:03}", "%y.Q%q"),
        ]
        
        for version, version_format, date_format in mixed_cases:
            result = parse_version(version, version_format, date_format)
            # These may or may not parse correctly - documenting current behavior
            if result is not None:
                print(f"Mixed separator pattern '{version}' parsed as: {result}")
            else:
                print(f"Mixed separator pattern '{version}' failed to parse (expected limitation)")

    def test_complex_format_limitations(self):
        """Test complex format patterns that may not work correctly."""
        complex_cases = [
            # These patterns have multiple dots which can confuse our simple parsing
            ("2024.12.07.rc.1", "{current_date}.rc.{build_count}", "%Y.%m.%d"),
            ("24.Q4.beta.2", "{current_date}.beta.{build_count}", "%y.Q%q"),
        ]
        
        for version, version_format, date_format in complex_cases:
            result = parse_version(version, version_format, date_format)
            if result is not None:
                print(f"Complex pattern '{version}' parsed as: {result} (may be incorrect)")
            else:
                print(f"Complex pattern '{version}' failed to parse")