"""Tree queries -- read-only inspection of node structures."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .walk import preorder


if TYPE_CHECKING:
    from collections.abc import Callable

    from ..tree import Node


__all__ = [
    "count",
    "depth",
    "find",
    "find_first",
    "size",
]


def find(root: Node, pred: Callable[[Node], bool]) -> list[Node]:
    """Find all nodes matching predicate (pre-order)."""
    return [node for node in preorder(root) if pred(node)]


def find_first(root: Node, pred: Callable[[Node], bool]) -> Node | None:
    """Find first matching node (pre-order), or None."""
    for node in preorder(root):
        if pred(node):
            return node
    return None


def count(root: Node, pred: Callable[[Node], bool] | None = None) -> int:
    """Count nodes matching predicate. None = count all."""
    if pred is None:
        return sum(1 for _ in preorder(root))
    return sum(1 for node in preorder(root) if pred(node))


def size(root: Node) -> int:
    """Total number of nodes."""
    return count(root)


def depth(root: Node) -> int:
    """Maximum depth. A leaf has depth 0."""
    if root.is_leaf:
        return 0
    return 1 + max(depth(c) for c in root.children)
