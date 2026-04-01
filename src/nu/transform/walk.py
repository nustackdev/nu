"""Tree walking -- traversal iterators over node structures.

All functions are lazy (generators) and non-mutating.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.terms import Node


__all__ = [
    "ancestors",
    "bfs",
    "leaves",
    "postorder",
    "preorder",
]


def preorder(root: Node) -> Iterator[Node]:
    """Depth-first pre-order. Yields root before children."""
    yield root
    for child in root.children:
        yield from preorder(child)


def postorder(root: Node) -> Iterator[Node]:
    """Depth-first post-order. Yields children before root."""
    for child in root.children:
        yield from postorder(child)
    yield root


def bfs(root: Node) -> Iterator[Node]:
    """Breadth-first traversal."""
    queue: deque[Node] = deque([root])
    while queue:
        node = queue.popleft()
        yield node
        queue.extend(node.children)


def leaves(root: Node) -> Iterator[Node]:
    """Yield only leaf nodes (no children)."""
    if root.is_leaf:
        yield root
    else:
        for child in root.children:
            yield from leaves(child)


def ancestors(target: Node, root: Node) -> list[Node] | None:
    """Path from root to target (exclusive of target), or None if not found.

    Uses identity comparison (is).
    """
    if root is target:
        return []
    for child in root.children:
        path = ancestors(target, child)
        if path is not None:
            return [root, *path]
    return None
