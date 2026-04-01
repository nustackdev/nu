"""_Node — immutable generic tree node (internal).

All operations return new nodes. Originals are never mutated.
This is the structural foundation — no semantics attached.

Generic over ``ChildT`` so subclasses can narrow the children type:
``Nu(_Node["Nu"])`` makes all Nu methods return ``Nu``, not ``_Node``.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Self


__all__ = [
    "_Node",
]


class _Node[ChildT]:
    """Immutable tree node, generic over child type. Internal.

    Args:
        *children: Child nodes.

    Access:
        children        — direct child nodes (tuple)
        is_leaf         — True if no children
        child_count     — number of direct children
        get_child       — child at index
        iter_children   — iterate over children
        has_child       — identity check against children

    Reconstruction:
        with_children   — replace all children, preserving node identity

    Modification (all return new nodes):
        append_child    — add child at end
        prepend_child   — add child at start
        insert_child    — add child at index
        remove_child    — remove child at index
        replace_child   — swap child at index
    """

    def __init__(self, *children: ChildT) -> None:
        """Initialize node with children."""
        self._children: tuple[ChildT, ...] = children

    # --- Access ---

    @property
    def children(self) -> tuple[ChildT, ...]:
        """Direct child nodes."""
        return self._children

    @property
    def is_leaf(self) -> bool:
        """True if this node has no children."""
        return not self._children

    @property
    def child_count(self) -> int:
        """Number of direct children."""
        return len(self._children)

    def get_child(self, index: int) -> ChildT:
        """Return child at index."""
        return self._children[index]

    def iter_children(self) -> Iterator[ChildT]:
        """Iterate over direct children."""
        return iter(self._children)

    def has_child(self, child: object) -> bool:
        """Check if child is a direct child by identity (``is``)."""
        return any(c is child for c in self._children)

    # --- Reconstruction ---

    def with_children(self, *children: ChildT) -> Self:
        """Shallow-copy this node with new children.

        Preserves all instance state (extra attributes set in __init__).
        Subclasses never need to override this.
        """
        if children == self._children:
            return self
        clone = copy.copy(self)
        clone._children = children
        return clone

    # --- Modification (immutable — all return new nodes) ---

    def append_child(self, child: ChildT) -> Self:
        """New node with child added at the end."""
        return self.with_children(*self._children, child)

    def prepend_child(self, child: ChildT) -> Self:
        """New node with child added at the start."""
        return self.with_children(child, *self._children)

    def insert_child(self, index: int, child: ChildT) -> Self:
        """New node with child inserted at index."""
        children = list(self._children)
        children.insert(index, child)
        return self.with_children(*children)

    def remove_child(self, index: int) -> Self:
        """New node with child at index removed."""
        children = list(self._children)
        del children[index]
        return self.with_children(*children)

    def replace_child(self, index: int, child: ChildT) -> Self:
        """New node with child at index replaced."""
        children = list(self._children)
        children[index] = child
        return self.with_children(*children)

    # --- Dunder methods ---

    def __bool__(self) -> bool:
        """A node always exists (always True)."""
        return True

    def __repr__(self) -> str:
        """Return ClassName(child_count=N) or ClassName() for leaves."""
        name = type(self).__name__
        if self._children:
            return f"{name}(child_count={self.child_count})"
        return f"{name}()"
