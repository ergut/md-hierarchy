"""Integration tests for split and merge operations."""

import pytest
from pathlib import Path
import shutil
import tempfile

from md_hierarchy.split import split_markdown
from md_hierarchy.merge import merge_markdown
from md_hierarchy.utils import INTRO_FILENAME, FRONTMATTER_FILENAME


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


class TestFileStructure:
    """Test that the new file structure with __intro__ and __frontmatter__ is created correctly."""

    def test_intro_files_always_created(self, simple_md, temp_dir):
        """Test that intro files are always created for all heading folders."""
        output_dir = temp_dir / "output"
        split_markdown(
            input_file=simple_md,
            output_dir=output_dir,
            target_level=3,
        )

        # Check that intro files exist at all folder levels
        intro_h1_intro = output_dir / "01-Introduction" / INTRO_FILENAME
        intro_h2_background = output_dir / "01-Introduction" / "01-Background" / INTRO_FILENAME
        results_h1_intro = output_dir / "02-Results" / INTRO_FILENAME

        assert intro_h1_intro.exists(), f"Intro file missing: {intro_h1_intro}"
        assert intro_h2_background.exists(), f"Intro file missing: {intro_h2_background}"
        assert results_h1_intro.exists(), f"Intro file missing: {results_h1_intro}"

    def test_intro_file_contains_heading(self, simple_md, temp_dir):
        """Test that intro files contain the heading even when there's no content."""
        output_dir = temp_dir / "output"
        split_markdown(
            input_file=simple_md,
            output_dir=output_dir,
            target_level=3,
        )

        # Check intro file for H2 "Background" which has content
        background_intro = output_dir / "01-Introduction" / "01-Background" / INTRO_FILENAME
        content = background_intro.read_text(encoding='utf-8')

        assert "## Background" in content
        assert "Background information goes here." in content

    def test_intro_file_with_empty_content(self, temp_dir):
        """Test that intro files are created even when heading has no direct content."""
        # Create markdown with heading that has no content before children
        md_content = """# Main

## Section

### Subsection1

Content here.

### Subsection2

More content.
"""
        md_file = temp_dir / "test.md"
        md_file.write_text(md_content, encoding='utf-8')

        output_dir = temp_dir / "output"
        split_markdown(
            input_file=md_file,
            output_dir=output_dir,
            target_level=3,
        )

        # Check that H2 "Section" has an intro file even though it has no content
        section_intro = output_dir / "01-Main" / "01-Section" / INTRO_FILENAME
        assert section_intro.exists()

        content = section_intro.read_text(encoding='utf-8')
        assert "## Section" in content
        # Should only have heading, no extra content
        lines = [l for l in content.strip().split('\n') if l.strip()]
        assert len(lines) == 1, f"Expected only heading, got: {lines}"

    def test_frontmatter_file_created(self, temp_dir):
        """Test that frontmatter file is created for content before first heading."""
        md_content = """This is frontmatter text.

It appears before any headings.

## Getting Started

Content here.
"""
        md_file = temp_dir / "test.md"
        md_file.write_text(md_content, encoding='utf-8')

        output_dir = temp_dir / "output"
        split_markdown(
            input_file=md_file,
            output_dir=output_dir,
            target_level=3,
        )

        # Check that frontmatter file exists at root
        frontmatter_file = output_dir / FRONTMATTER_FILENAME
        assert frontmatter_file.exists(), f"Frontmatter file not created: {frontmatter_file}"

        content = frontmatter_file.read_text(encoding='utf-8')
        assert "This is frontmatter text." in content
        assert "It appears before any headings." in content

    def test_no_frontmatter_when_empty(self, simple_md, temp_dir):
        """Test that frontmatter file is NOT created when there's no content before H1."""
        output_dir = temp_dir / "output"
        split_markdown(
            input_file=simple_md,
            output_dir=output_dir,
            target_level=3,
        )

        # simple_md starts with H1, so no frontmatter file should exist
        frontmatter_file = output_dir / FRONTMATTER_FILENAME
        assert not frontmatter_file.exists(), "Frontmatter file should not exist when there's no pre-H1 content"

    def test_file_sorting_order(self, simple_md, temp_dir):
        """Test that intro file sorts first (00- prefix)."""
        output_dir = temp_dir / "output"
        split_markdown(
            input_file=simple_md,
            output_dir=output_dir,
            target_level=3,
        )

        # Get files in Background folder
        background_dir = output_dir / "01-Introduction" / "01-Background"
        files = sorted([f.name for f in background_dir.iterdir() if f.is_file()])

        # Intro file should be first due to 00- prefix
        assert files[0] == INTRO_FILENAME, f"Intro file should sort first, got: {files}"
        assert files[1] == "01-Problem-Statement.md"
        assert files[2] == "02-Research-Gap.md"


class TestFrontmatterRoundTrip:
    """Test round-trip with frontmatter content."""

    def test_frontmatter_round_trip(self, temp_dir):
        """Test that frontmatter content is preserved in round-trip."""
        original_content = """Frontmatter paragraph 1.

Frontmatter paragraph 2.

## Section One

Section content.

### Subsection

Subsection content.
"""
        md_file = temp_dir / "test.md"
        md_file.write_text(original_content, encoding='utf-8')

        # Split
        split_dir = temp_dir / "split"
        split_markdown(
            input_file=md_file,
            output_dir=split_dir,
            target_level=3,
        )

        # Merge
        merged_file = temp_dir / "merged.md"
        merge_markdown(
            input_dir=split_dir,
            output_file=merged_file,
        )

        # Compare
        original = md_file.read_text(encoding='utf-8').strip()
        merged = merged_file.read_text(encoding='utf-8').strip()

        assert original == merged, "Frontmatter should be preserved in round-trip"
