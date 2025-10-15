"""Markdown parser to build heading hierarchy."""

import re
from typing import List

from .types import HeadingNode
from .utils import strip_heading_attributes


def parse_markdown(content: str) -> HeadingNode:
    """Parse markdown content into a hierarchical tree of headings.

    Uses a simple regex-based approach to extract headings and content.

    Args:
        content: Markdown file content

    Returns:
        Root HeadingNode representing the document structure
    """
    lines = content.split('\n')

    # Create synthetic root node
    root = HeadingNode(level=0, title="__root__")

    # Find all headings with their line numbers
    headings = []
    for i, line in enumerate(lines):
        match = re.match(r'^(#{1,4})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title_with_attrs = match.group(2).strip()
            title, attrs = strip_heading_attributes(title_with_attrs)
            headings.append({
                'line_num': i,
                'level': level,
                'title': title,
                'attributes': attrs if attrs else None,
            })

    if not headings:
        # No headings - all content is frontmatter
        root.content = content.strip()
        return root

    # Extract frontmatter (content before first heading)
    if headings[0]['line_num'] > 0:
        frontmatter = '\n'.join(lines[:headings[0]['line_num']]).strip()
        if frontmatter:
            frontmatter_node = HeadingNode(level=0, title="__frontmatter__", content=frontmatter)
            root.children.append(frontmatter_node)

    # Build tree structure by processing each heading
    for i, heading_info in enumerate(headings):
        # Find the content for this heading
        start_line = heading_info['line_num'] + 1  # Line after the heading

        # Find where this heading's content ends (next heading at same or higher level)
        end_line = len(lines)
        for j in range(i + 1, len(headings)):
            if headings[j]['level'] <= heading_info['level']:
                end_line = headings[j]['line_num']
                break

        # Extract direct content (before any child headings)
        direct_content_end = end_line
        for j in range(i + 1, len(headings)):
            if headings[j]['level'] > heading_info['level']:
                # This is a child heading, content ends here
                direct_content_end = headings[j]['line_num']
                break

        # Get the content
        content_lines = lines[start_line:direct_content_end]
        content = '\n'.join(content_lines).strip()

        # Create node
        node = HeadingNode(
            level=heading_info['level'],
            title=heading_info['title'] or "",
            content=content,
            attributes=heading_info['attributes'],
        )

        # Find parent and add to tree
        _add_to_tree(root, node)

    return root


def _add_to_tree(root: HeadingNode, node: HeadingNode) -> None:
    """Add a node to the tree at the appropriate location.

    Args:
        root: Root node of the tree
        node: Node to add
    """
    # Find the appropriate parent for this node
    parent = _find_parent(root, node.level)
    parent.children.append(node)


def _find_parent(current: HeadingNode, target_level: int) -> HeadingNode:
    """Find the parent node for a heading at target_level.

    The parent is the most recent node at level (target_level - 1).

    Args:
        current: Current node to search from (usually root)
        target_level: Level of the node we want to add

    Returns:
        The parent node
    """
    # If we're at the root (level 0) and looking for level 1, root is the parent
    if current.level == 0 and target_level == 1:
        return current

    # If current level is one less than target, check if we have children
    if current.level == target_level - 1:
        return current

    # Otherwise, recursively check children (depth-first, so we get the most recent)
    for child in reversed(current.children):
        if child.level < target_level:
            # This child could be a parent or ancestor
            result = _find_parent(child, target_level)
            if result:
                return result

    # If no suitable child found, current is the parent
    # (handles skipped levels - e.g., H1 -> H3)
    return current
