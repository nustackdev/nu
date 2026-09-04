"""Tree walking -- traversal iterators over Term structures.

All functions are lazy (generators) and non-mutating. Domain-free: they
touch only ``._children`` and identity, so they work on any Term tree.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterator

    from nu.lang import Nu


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
    for child in root._children:
        yield from preorder(child)


def postorder(root: Nu) -> Iterator[Nu]:
    """Depth-first post-order. Yields children before root."""
    for child in root._children:
        yield from postorder(child)
    yield root


def bfs(root: Nu) -> Iterator[Nu]:
    """Breadth-first traversal."""
    queue: deque[Nu] = deque([root])
    while queue:
        node = queue.popleft()
        yield node
        queue.extend(node._children)


def leaves(root: Nu) -> Iterator[Nu]:
    """Yield only leaf nodes (no children)."""
    if not root._children:
        yield root
    else:
        for child in root._children:
            yield from leaves(child)


def ancestors(target: Nu, root: Nu) -> list[Nu] | None:
    """Path from root to target (exclusive of target), or None if not found.

    Uses identity comparison (``is``).
    """
    if root is target:
        return []
    for child in root._children:
        path = ancestors(target, child)
        if path is not None:
            return [root, *path]
    return None
