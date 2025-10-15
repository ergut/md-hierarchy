"""Merge hierarchical folder structure back into markdown file."""

import re
from pathlib import Path
from typing import List, Tuple

from .types import MergeResult
from .utils import validate_directory_exists


def merge_markdown(
    input_dir: Path,
    output_file: Path,
    verbose: bool = False,
) -> MergeResult:
    """Merge hierarchical folder structure back into a single markdown file.

    Args:
        input_dir: Path to input directory
        output_file: Path to output markdown file
        verbose: Print detailed operation log

    Returns:
        MergeResult with operation statistics

    Raises:
        FileNotFoundError: If input directory doesn't exist
        NotADirectoryError: If input path is not a directory
    """
    validate_directory_exists(input_dir)

    if verbose:
        print(f"Merging from {input_dir}...")

    lines = []
    files_merged_counter = {"count": 0}

    # Process directory recursively
    _process_directory(input_dir, lines, level=1, verbose=verbose, files_merged_counter=files_merged_counter)
    files_merged = files_merged_counter["count"]

    # Write output file
    content = '\n'.join(lines)

    # Clean up: ensure single blank line between sections, no trailing spaces
    content = _clean_spacing(content)

    output_file.write_text(content, encoding='utf-8')

    if verbose:
        print(f"Merged {files_merged} files into {output_file}")

    return MergeResult(
        files_merged=files_merged,
        output_path=str(output_file),
    )


def _process_directory(
    dir_path: Path,
    lines: List[str],
    level: int,
    verbose: bool,
    files_merged_counter: dict,
) -> None:
    """Recursively process a directory and build markdown content.

    Args:
        dir_path: Directory to process
        lines: List of output lines (modified in place)
        level: Current heading level
        verbose: Verbose output flag
        files_merged_counter: Counter for files merged (modified in place)
    """
    # Get all items in directory, sorted
    items = sorted(dir_path.iterdir(), key=lambda x: _sort_key(x.name))

    # First, process README.md if it exists (parent content)
    readme_path = dir_path / "README.md"
    if readme_path.exists() and readme_path.is_file():
        _add_file_content(readme_path, lines, verbose)
        files_merged_counter["count"] += 1

    # Then process numbered files and folders
    for item in items:
        if item.name == "README.md":
            continue  # Already processed

        if item.is_file() and item.suffix == ".md":
            # Process markdown file
            _add_file_content(item, lines, verbose)
            files_merged_counter["count"] += 1

        elif item.is_dir():
            # Process subdirectory recursively
            _process_directory(
                item,
                lines,
                level + 1,
                verbose,
                files_merged_counter,
            )


def _add_file_content(file_path: Path, lines: List[str], verbose: bool) -> None:
    """Add content from a markdown file to lines.

    Args:
        file_path: Path to markdown file
        lines: List of output lines (modified in place)
        verbose: Verbose output flag
    """
    content = file_path.read_text(encoding='utf-8').strip()

    if content:
        # Add blank line separator if we have existing content
        if lines and lines[-1] != "":
            lines.append("")

        lines.append(content)

        if verbose:
            print(f"Merged: {file_path}")


def _sort_key(name: str) -> Tuple[int, str]:
    """Generate sort key for file/folder names.

    Numbered items (01-Name, 02-Name) sort by number.
    Non-numbered items sort alphabetically after numbered ones.

    Args:
        name: File or folder name

    Returns:
        Tuple for sorting (priority, name)
    """
    # Match pattern: NN-Name or just Name
    match = re.match(r'^(\d+)-(.+?)(?:\.md)?$', name)
    if match:
        number = int(match.group(1))
        return (number, match.group(2))

    # Special case: README.md always first
    if name == "README.md":
        return (0, "")

    # Non-numbered items sort after numbered ones
    return (9999, name)


def _clean_spacing(content: str) -> str:
    """Clean spacing in merged content.

    Rules:
    - Remove trailing whitespace from lines
    - Ensure single blank line between sections
    - No blank lines at start
    - Single newline at end of file

    Args:
        content: Raw merged content

    Returns:
        Cleaned content
    """
    lines = content.split('\n')

    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in lines]

    # Remove leading blank lines
    while lines and not lines[0]:
        lines.pop(0)

    # Remove trailing blank lines (except one)
    while len(lines) > 1 and not lines[-1]:
        lines.pop()

    # Collapse multiple consecutive blank lines into single blank line
    cleaned_lines = []
    prev_blank = False

    for line in lines:
        is_blank = not line

        if is_blank:
            if not prev_blank:
                cleaned_lines.append(line)
            prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False

    # Ensure single newline at end
    result = '\n'.join(cleaned_lines)
    if result and not result.endswith('\n'):
        result += '\n'

    return result
