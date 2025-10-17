"""Split markdown files into hierarchical folder structure."""

from pathlib import Path
from typing import Optional
import shutil

from .types import HeadingNode, SplitResult
from .parser import parse_markdown
from .utils import (
    sanitize_filename,
    format_number_prefix,
    DuplicateNameTracker,
    validate_file_exists,
    validate_level,
    INTRO_FILENAME,
    FRONTMATTER_FILENAME,
)


def split_markdown(
    input_file: Path,
    output_dir: Path,
    target_level: int = 3,
    overwrite: bool = False,
    verbose: bool = False,
    dry_run: bool = False,
) -> SplitResult:
    """Split a markdown file into hierarchical folder structure.

    Args:
        input_file: Path to input markdown file
        output_dir: Path to output directory
        target_level: Heading level to extract as files (1-4)
        overwrite: Whether to overwrite existing output directory
        verbose: Print detailed operation log
        dry_run: Show what would be done without writing files

    Returns:
        SplitResult with operation statistics

    Raises:
        FileNotFoundError: If input file doesn't exist
        FileExistsError: If output directory exists and overwrite=False
        ValueError: If target_level is not 1-4
    """
    # Validate inputs
    validate_file_exists(input_file)
    validate_level(target_level)

    # Check output directory
    if output_dir.exists() and not overwrite:
        raise FileExistsError(
            f"Output directory already exists: {output_dir}\n"
            "Use --overwrite to overwrite existing directory."
        )

    # Parse markdown
    if verbose:
        print(f"Parsing {input_file}...")

    content = input_file.read_text(encoding='utf-8')
    root = parse_markdown(content)

    # Initialize statistics
    sections_count = 0
    files_count = 0
    folders_count = 0

    # Create output directory
    if not dry_run:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        folders_count += 1
    else:
        print(f"Would create directory: {output_dir}")
        folders_count += 1

    # Initialize duplicate tracker
    dup_tracker = DuplicateNameTracker()

    # Process frontmatter if exists
    frontmatter_node = next(
        (child for child in root.children if child.title == "__frontmatter__"),
        None
    )
    if frontmatter_node and frontmatter_node.content:
        frontmatter_path = output_dir / FRONTMATTER_FILENAME
        if not dry_run:
            frontmatter_path.write_text(frontmatter_node.content + '\n', encoding='utf-8')
            if verbose:
                print(f"Created: {frontmatter_path}")
            files_count += 1
        else:
            print(f"Would create: {frontmatter_path}")
            files_count += 1

    # Process regular headings
    regular_children = [
        child for child in root.children
        if child.title != "__frontmatter__"
    ]

    # Track untitled section counter and stats
    untitled_counter = {"count": 0}
    stats = {"sections": 0, "files": 0, "folders": 0}

    for node in regular_children:
        _process_node(
            node=node,
            parent_path=output_dir,
            target_level=target_level,
            current_depth=1,
            index=regular_children.index(node),
            total_siblings=len(regular_children),
            dup_tracker=dup_tracker,
            verbose=verbose,
            dry_run=dry_run,
            untitled_counter=untitled_counter,
            stats=stats,
        )

    sections_count = stats["sections"]
    files_count += stats["files"]
    folders_count += stats["folders"]

    # Adjust total folders (we already counted output_dir)
    return SplitResult(
        sections_count=sections_count,
        files_count=files_count + (1 if frontmatter_node else 0),
        folders_count=folders_count,
    )


def _process_node(
    node: HeadingNode,
    parent_path: Path,
    target_level: int,
    current_depth: int,
    index: int,
    total_siblings: int,
    dup_tracker: DuplicateNameTracker,
    verbose: bool,
    dry_run: bool,
    untitled_counter: dict,
    stats: dict,
    parent_key: str = "",
) -> None:
    """Recursively process a heading node and create files/folders.

    Args:
        node: HeadingNode to process
        parent_path: Parent directory path
        target_level: Target extraction level
        current_depth: Current depth in hierarchy
        index: Index among siblings
        total_siblings: Total number of siblings
        dup_tracker: Duplicate name tracker
        verbose: Verbose output flag
        dry_run: Dry run flag
        untitled_counter: Counter for untitled sections
        stats: Statistics dictionary (modified in place)
        parent_key: Parent key for duplicate tracking
    """
    # Handle empty/untitled headings
    title = node.title.strip()
    if not title:
        untitled_counter["count"] += 1
        title = f"Untitled-Section-{untitled_counter['count']}"
        node.title = title

    # Sanitize and create unique name
    sanitized = sanitize_filename(title)
    unique_name = dup_tracker.get_unique_name(sanitized, parent_key)

    # Format with number prefix
    prefix = format_number_prefix(index, total_siblings)
    dir_name = f"{prefix}-{unique_name}"
    node_path = parent_path / dir_name
    new_parent_key = f"{parent_key}/{unique_name}"

    # Check if we're at the target level
    if node.level == target_level:
        # Extract as file
        _extract_as_file(
            node=node,
            parent_path=parent_path,
            file_name=f"{dir_name}.md",
            verbose=verbose,
            dry_run=dry_run,
        )
        stats["sections"] += 1
        stats["files"] += 1

    elif node.level < target_level:
        # Create folder for this heading level
        if not dry_run:
            node_path.mkdir(parents=True, exist_ok=True)
            if verbose:
                print(f"Created directory: {node_path}")
        else:
            if verbose:
                print(f"Would create directory: {node_path}")

        stats["folders"] += 1

        # Always create intro file (even if content is empty)
        _write_intro(
            node=node,
            path=node_path,
            verbose=verbose,
            dry_run=dry_run,
        )
        stats["files"] += 1

        # Handle skipped levels - insert synthetic folders
        if node.children:
            first_child_level = node.children[0].level
            expected_level = node.level + 1

            if first_child_level > expected_level:
                # Skipped levels detected
                synthetic_path = node_path / "00-Content"
                if not dry_run:
                    synthetic_path.mkdir(exist_ok=True)
                    if verbose:
                        print(f"Created synthetic directory for skipped levels: {synthetic_path}")
                else:
                    if verbose:
                        print(f"Would create synthetic directory: {synthetic_path}")
                stats["folders"] += 1
                node_path = synthetic_path

        # Process children
        for i, child in enumerate(node.children):
            _process_node(
                node=child,
                parent_path=node_path,
                target_level=target_level,
                current_depth=current_depth + 1,
                index=i,
                total_siblings=len(node.children),
                dup_tracker=dup_tracker,
                verbose=verbose,
                dry_run=dry_run,
                untitled_counter=untitled_counter,
                stats=stats,
                parent_key=new_parent_key,
            )

    # If level > target_level, it's included in parent's content (depth limit is 4)


def _extract_as_file(
    node: HeadingNode,
    parent_path: Path,
    file_name: str,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Extract a node as a standalone markdown file.

    Args:
        node: HeadingNode to extract
        parent_path: Parent directory path
        file_name: Output file name
        verbose: Verbose output flag
        dry_run: Dry run flag
    """
    file_path = parent_path / file_name

    # Build content: heading + content + all children (depth limit 4)
    lines = []

    # Add heading with attributes if present
    heading_marker = '#' * node.level
    heading_line = f"{heading_marker} {node.title}"
    if node.attributes:
        heading_line += f" {node.attributes}"
    lines.append(heading_line)

    # Add direct content
    if node.content.strip():
        lines.append("")
        lines.append(node.content.rstrip())

    # Add all children (they're within depth limit of 4)
    _append_children_content(node, lines)

    content = '\n'.join(lines) + '\n'

    if not dry_run:
        file_path.write_text(content, encoding='utf-8')
        if verbose:
            print(f"Created: {file_path}")
    else:
        if verbose:
            print(f"Would create: {file_path}")


def _write_intro(
    node: HeadingNode,
    path: Path,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Write intro file for a folder (parent heading and its direct content).

    Args:
        node: HeadingNode with heading and content
        path: Directory path
        verbose: Verbose output flag
        dry_run: Dry run flag
    """
    intro_path = path / INTRO_FILENAME

    lines = []

    # Add heading with attributes
    heading_marker = '#' * node.level
    heading_line = f"{heading_marker} {node.title}"
    if node.attributes:
        heading_line += f" {node.attributes}"
    lines.append(heading_line)

    # Add content (only direct content, not children)
    if node.content.strip():
        lines.append("")
        lines.append(node.content.rstrip())

    content = '\n'.join(lines) + '\n'

    if not dry_run:
        intro_path.write_text(content, encoding='utf-8')
        if verbose:
            print(f"Created: {intro_path}")
    else:
        if verbose:
            print(f"Would create: {intro_path}")


def _append_children_content(node: HeadingNode, lines: list) -> None:
    """Recursively append children content to lines.

    Args:
        node: Parent node
        lines: List of lines to append to
    """
    for child in node.children:
        lines.append("")

        # Add child heading
        heading_marker = '#' * child.level
        heading_line = f"{heading_marker} {child.title}"
        if child.attributes:
            heading_line += f" {child.attributes}"
        lines.append(heading_line)

        # Add child content
        if child.content.strip():
            lines.append("")
            lines.append(child.content.rstrip())

        # Recursively add deeper children
        _append_children_content(child, lines)
