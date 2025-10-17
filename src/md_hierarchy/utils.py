"""Utility functions for md-hierarchy."""

import re
from pathlib import Path
from typing import Dict, Set


# Special filenames
INTRO_FILENAME = "00-__intro__.md"
FRONTMATTER_FILENAME = "00-__frontmatter__.md"


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Sanitize a heading title for use as a filename or folder name.

    Rules:
    - Replace spaces with hyphens
    - Remove special characters: / \\ : * ? " < > |
    - Limit length to max_length characters
    - Preserve case

    Args:
        title: The heading title to sanitize
        max_length: Maximum length for the sanitized name

    Returns:
        Sanitized filename/folder name
    """
    if not title or not title.strip():
        return "Untitled"

    # Replace spaces with hyphens
    sanitized = title.replace(" ", "-")

    # Remove special characters
    sanitized = re.sub(r'[/\\:*?"<>|]', "", sanitized)

    # Remove multiple consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)

    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-')

    return sanitized or "Untitled"


def strip_heading_attributes(title: str) -> tuple[str, str]:
    """Strip attributes from heading title.

    Examples:
        "My Section {#custom-id .class}" -> ("My Section", "{#custom-id .class}")
        "Plain Title" -> ("Plain Title", "")

    Args:
        title: Heading title possibly with attributes

    Returns:
        Tuple of (clean_title, attributes)
    """
    # Match attributes pattern: {#id .class key=value}
    match = re.search(r'\s*\{[^}]+\}\s*$', title)
    if match:
        attributes = match.group().strip()
        clean_title = title[:match.start()].strip()
        return clean_title, attributes
    return title.strip(), ""


class DuplicateNameTracker:
    """Tracks duplicate names and generates unique suffixes."""

    def __init__(self):
        """Initialize the tracker."""
        self._counters: Dict[str, int] = {}
        self._seen: Set[str] = set()

    def get_unique_name(self, base_name: str, parent_path: str = "") -> str:
        """Get a unique name, adding suffix if necessary.

        Args:
            base_name: The base name (without number prefix)
            parent_path: Parent path to track duplicates in context

        Returns:
            Unique name with suffix if needed (e.g., "Results-2")
        """
        key = f"{parent_path}/{base_name}"

        if key not in self._seen:
            self._seen.add(key)
            return base_name

        # Name exists, find next available suffix
        if key not in self._counters:
            self._counters[key] = 2
        else:
            self._counters[key] += 1

        suffix = self._counters[key]
        unique_name = f"{base_name}-{suffix}"
        self._seen.add(f"{parent_path}/{unique_name}")

        return unique_name


def format_number_prefix(index: int, total: int) -> str:
    """Format a number prefix with appropriate zero-padding.

    Args:
        index: The index (0-based)
        total: Total number of items

    Returns:
        Formatted prefix like "01", "02", "99", "001" (adapts to total)
    """
    # Determine number of digits needed
    digits = len(str(total))
    # Ensure at least 2 digits
    digits = max(2, digits)

    return f"{index + 1:0{digits}d}"


def validate_level(level: int) -> None:
    """Validate that level is in range 1-4.

    Args:
        level: Heading level to validate

    Raises:
        ValueError: If level is not 1-4
    """
    if not isinstance(level, int) or not 1 <= level <= 4:
        raise ValueError(f"Level must be an integer between 1 and 4, got {level}")


def validate_file_exists(file_path: Path) -> None:
    """Validate that a file exists and is readable.

    Args:
        file_path: Path to validate

    Raises:
        FileNotFoundError: If file doesn't exist
        IsADirectoryError: If path is a directory
        PermissionError: If file isn't readable
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a regular file: {file_path}")


def validate_directory_exists(dir_path: Path) -> None:
    """Validate that a directory exists.

    Args:
        dir_path: Path to validate

    Raises:
        FileNotFoundError: If directory doesn't exist
        NotADirectoryError: If path is not a directory
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
