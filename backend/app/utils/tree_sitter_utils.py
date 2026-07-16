"""
TestPilot AI — Tree-sitter Utilities.

Provides helper utilities for working with Tree-sitter AST nodes,
such as extracting code text, node spans, and matching language extensions.
"""

from __future__ import annotations

from typing import Any


def get_node_text(node: Any, source_code: bytes | str) -> str:
    """Extract the exact source code slice represented by a Tree-sitter node.

    Args:
        node: The Tree-sitter AST node.
        source_code: The raw file content (bytes or string).

    Returns:
        The matched code string segment.
    """
    if isinstance(source_code, str):
        return source_code[node.start_byte : node.end_byte]
    return source_code[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def get_node_span(node: Any) -> tuple[int, int]:
    """Get the 1-indexed line start and line end range of a node.

    Args:
        node: The Tree-sitter AST node.

    Returns:
        A tuple of (start_line, end_line) (1-indexed).
    """
    return (node.start_point[0] + 1, node.end_point[0] + 1)
