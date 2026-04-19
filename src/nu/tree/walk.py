"""Tree walking -- traversal iterators over node structures.

All functions are lazy (generators) and non-mutating.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.terms import Nu


__all__ = [
    "ancestors",
    "bfs",
    "leaves",
    "postorder",
    "preorder",
]


def preorder(root: Nu) -> Iterator[Nu]:
    """Depth-first pre-order. Yields root before children."""
    yield root
    for child in root.children:
        yield from preorder(child)


def postorder(root: Nu) -> Iterator[Nu]:
    """Depth-first post-order. Yields children before root."""
    for child in root.children:
        yield from postorder(child)
    yield root


def bfs(root: Nu) -> Iterator[Nu]:
    """Breadth-first traversal."""
    queue: deque[Nu] = deque([root])
    while queue:
        node = queue.popleft()
        yield node
        queue.extend(node.children)


def leaves(root: Nu) -> Iterator[Nu]:
    """Yield only leaf nodes (no children)."""
    if root._is_leaf:
        yield root
    else:
        for child in root.children:
            yield from leaves(child)


def ancestors(target: Nu, root: Nu) -> list[Nu] | None:
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
