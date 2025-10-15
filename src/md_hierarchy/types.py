"""Type definitions for md-hierarchy."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HeadingNode:
    """Represents a heading section in the markdown hierarchy.

    Attributes:
        level: Heading level (1-4 for H1-H4, 0 for internal root/frontmatter nodes)
        title: Original heading text (without the # markers)
        content: Direct content under this heading (before any child headings)
        children: Child heading nodes
        attributes: Optional heading attributes like {#id .class}
    """
    level: int
    title: str
    content: str = ""
    children: List['HeadingNode'] = field(default_factory=list)
    attributes: Optional[str] = None

    def __post_init__(self):
        """Validate heading level."""
        if not 0 <= self.level <= 4:
            raise ValueError(f"Heading level must be 0-4, got {self.level}")


@dataclass
class SplitResult:
    """Result of a split operation.

    Attributes:
        sections_count: Number of sections extracted
        files_count: Total number of files created
        folders_count: Total number of folders created
    """
    sections_count: int
    files_count: int
    folders_count: int


@dataclass
class MergeResult:
    """Result of a merge operation.

    Attributes:
        files_merged: Number of files merged
        output_path: Path to the output markdown file
    """
    files_merged: int
    output_path: str
