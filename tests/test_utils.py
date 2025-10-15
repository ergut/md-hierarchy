"""Tests for utility functions."""

import pytest
from md_hierarchy.utils import (
    sanitize_filename,
    strip_heading_attributes,
    DuplicateNameTracker,
    format_number_prefix,
    validate_level,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_title(self):
        assert sanitize_filename("Introduction") == "Introduction"

    def test_spaces_to_hyphens(self):
        assert sanitize_filename("Problem Statement") == "Problem-Statement"

    def test_special_characters(self):
        assert sanitize_filename("What/Why:How?") == "WhatWhyHow"

    def test_multiple_hyphens(self):
        assert sanitize_filename("A  --  B") == "A-B"

    def test_length_limit(self):
        long_title = "A" * 100
        result = sanitize_filename(long_title, max_length=50)
        assert len(result) == 50

    def test_empty_string(self):
        assert sanitize_filename("") == "Untitled"
        assert sanitize_filename("   ") == "Untitled"

    def test_only_special_chars(self):
        assert sanitize_filename("///:::") == "Untitled"


class TestStripHeadingAttributes:
    """Tests for strip_heading_attributes function."""

    def test_no_attributes(self):
        title, attrs = strip_heading_attributes("Plain Title")
        assert title == "Plain Title"
        assert attrs == ""

    def test_with_attributes(self):
        title, attrs = strip_heading_attributes("My Section {#custom-id .class}")
        assert title == "My Section"
        assert attrs == "{#custom-id .class}"

    def test_complex_attributes(self):
        title, attrs = strip_heading_attributes("Title {#id .c1 .c2 key=value}")
        assert title == "Title"
        assert attrs == "{#id .c1 .c2 key=value}"


class TestDuplicateNameTracker:
    """Tests for DuplicateNameTracker class."""

    def test_unique_names(self):
        tracker = DuplicateNameTracker()
        assert tracker.get_unique_name("Introduction") == "Introduction"
        assert tracker.get_unique_name("Background") == "Background"

    def test_duplicate_names(self):
        tracker = DuplicateNameTracker()
        assert tracker.get_unique_name("Results") == "Results"
        assert tracker.get_unique_name("Results") == "Results-2"
        assert tracker.get_unique_name("Results") == "Results-3"

    def test_duplicate_in_different_contexts(self):
        tracker = DuplicateNameTracker()
        assert tracker.get_unique_name("Analysis", "/chapter1") == "Analysis"
        assert tracker.get_unique_name("Analysis", "/chapter2") == "Analysis"
        # Same context
        assert tracker.get_unique_name("Analysis", "/chapter1") == "Analysis-2"


class TestFormatNumberPrefix:
    """Tests for format_number_prefix function."""

    def test_small_numbers(self):
        assert format_number_prefix(0, 9) == "01"
        assert format_number_prefix(8, 9) == "09"

    def test_large_numbers(self):
        assert format_number_prefix(0, 100) == "001"
        assert format_number_prefix(99, 100) == "100"

    def test_very_large(self):
        assert format_number_prefix(0, 1000) == "0001"


class TestValidateLevel:
    """Tests for validate_level function."""

    def test_valid_levels(self):
        for level in [1, 2, 3, 4]:
            validate_level(level)  # Should not raise

    def test_invalid_levels(self):
        with pytest.raises(ValueError):
            validate_level(0)
        with pytest.raises(ValueError):
            validate_level(5)
        with pytest.raises(ValueError):
            validate_level(-1)
