"""Tree queries -- read-only inspection of node structures."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Nu

from .walk import preorder


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = [
    "count",
    "depth",
    "find",
    "find_first",
    "size",
]


def find[N: Nu](root: N, pred: Callable[[Nu], bool]) -> list[N]:
    """Find all nodes matching predicate (pre-order)."""
    return [node for node in preorder(root) if pred(node)]  # type: ignore[misc]


def find_first[N: Nu](root: N, pred: Callable[[Nu], bool]) -> N | None:
    """Find first matching node (pre-order), or None."""
    for node in preorder(root):
        if pred(node):
            return node  # type: ignore[return-value]
    return None


def count(root: Nu, pred: Callable[[Nu], bool] | None = None) -> int:
    """Count nodes matching predicate. None = count all."""
    if pred is None:
        return sum(1 for _ in preorder(root))
    return sum(1 for node in preorder(root) if pred(node))


def size(root: Nu) -> int:
    """Total number of nodes."""
    return count(root)


def depth(root: Nu) -> int:
    """Maximum depth. A leaf has depth 0."""
    if root.is_leaf:
        return 0
    return 1 + max(depth(c) for c in root.children)
