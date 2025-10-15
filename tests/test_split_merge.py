"""Integration tests for split and merge operations."""

import pytest
from pathlib import Path
import shutil
import tempfile

from md_hierarchy.split import split_markdown
from md_hierarchy.merge import merge_markdown


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def simple_md(temp_dir):
    """Create a simple test markdown file."""
    content = """# Introduction

This is the introduction section.

## Background

Background information goes here.

### Problem Statement

The problem we're solving.

### Research Gap

There's a gap in research.

# Results

Our results are here.
"""
    md_file = temp_dir / "test.md"
    md_file.write_text(content, encoding='utf-8')
    return md_file


class TestSplitOperation:
    """Tests for split operation."""

    def test_split_basic(self, simple_md, temp_dir):
        """Test basic split operation."""
        output_dir = temp_dir / "output"

        result = split_markdown(
            input_file=simple_md,
            output_dir=output_dir,
            target_level=3,
            overwrite=False,
            verbose=False,
            dry_run=False,
        )

        # Check that output directory was created
        assert output_dir.exists()
        assert output_dir.is_dir()

        # Check statistics
        assert result.sections_count == 2  # Problem Statement, Research Gap
        assert result.files_count > 0
        assert result.folders_count > 0

    def test_split_dry_run(self, simple_md, temp_dir):
        """Test split with dry run."""
        output_dir = temp_dir / "output"

        result = split_markdown(
            input_file=simple_md,
            output_dir=output_dir,
            target_level=3,
            dry_run=True,
        )

        # Output directory should not be created in dry run
        assert not output_dir.exists()

        # But we should get statistics
        assert result.sections_count == 2

    def test_split_overwrite(self, simple_md, temp_dir):
        """Test split with overwrite."""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # First split should fail without overwrite
        with pytest.raises(FileExistsError):
            split_markdown(
                input_file=simple_md,
                output_dir=output_dir,
                target_level=3,
                overwrite=False,
            )

        # Second split should succeed with overwrite
        result = split_markdown(
            input_file=simple_md,
            output_dir=output_dir,
            target_level=3,
            overwrite=True,
        )
        assert result.files_count > 0

    def test_split_different_levels(self, simple_md, temp_dir):
        """Test split at different levels."""
        # Level 2
        output_dir_2 = temp_dir / "output2"
        result2 = split_markdown(
            input_file=simple_md,
            output_dir=output_dir_2,
            target_level=2,
        )
        assert result2.sections_count == 1  # Only "Background" has children at level 2

        # Level 3
        output_dir_3 = temp_dir / "output3"
        result3 = split_markdown(
            input_file=simple_md,
            output_dir=output_dir_3,
            target_level=3,
        )
        assert result3.sections_count == 2  # Problem Statement, Research Gap


class TestMergeOperation:
    """Tests for merge operation."""

    def test_merge_basic(self, simple_md, temp_dir):
        """Test basic merge operation."""
        # First split
        split_dir = temp_dir / "split"
        split_markdown(
            input_file=simple_md,
            output_dir=split_dir,
            target_level=3,
        )

        # Then merge
        output_file = temp_dir / "merged.md"
        result = merge_markdown(
            input_dir=split_dir,
            output_file=output_file,
            verbose=False,
        )

        # Check that output file was created
        assert output_file.exists()
        assert output_file.is_file()

        # Check statistics
        assert result.files_merged > 0

        # Check content exists
        content = output_file.read_text(encoding='utf-8')
        assert len(content) > 0
        assert "# Introduction" in content


class TestRoundTrip:
    """Test round-trip: split then merge."""

    def test_round_trip_basic(self, simple_md, temp_dir):
        """Test that split -> merge produces similar content."""
        # Split
        split_dir = temp_dir / "split"
        split_markdown(
            input_file=simple_md,
            output_dir=split_dir,
            target_level=3,
        )

        # Merge
        merged_file = temp_dir / "merged.md"
        merge_markdown(
            input_dir=split_dir,
            output_file=merged_file,
        )

        # Read both files
        original = simple_md.read_text(encoding='utf-8').strip()
        merged = merged_file.read_text(encoding='utf-8').strip()

        # They should have the same headings (normalize whitespace)
        original_lines = [line.strip() for line in original.split('\n') if line.strip()]
        merged_lines = [line.strip() for line in merged.split('\n') if line.strip()]

        # Check that headings are preserved
        original_headings = [line for line in original_lines if line.startswith('#')]
        merged_headings = [line for line in merged_lines if line.startswith('#')]

        assert original_headings == merged_headings
