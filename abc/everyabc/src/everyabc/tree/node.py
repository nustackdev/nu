"""Node — immutable generic tree node.

All operations return new nodes. Originals are never mutated.
This is the structural foundation — no semantics attached.

Generic over ``ChildT`` so subclasses can narrow the children type:
``Exec(Node["Exec"])`` makes all Exec methods return ``Exec``, not ``Node``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload


if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Self


__all__ = [
    "Node",
]


class Node[ChildT]:
    """Immutable tree node, generic over child type.

    Args:
        *children: Child nodes.

    Access:
        children       — direct child nodes (tuple)
        is_leaf        — True if no children
        child_count    — number of direct children

    Reconstruction:
        with_children  — replace all children, preserving node identity

    Modification (all return new nodes):
        append         — add child at end
        prepend        — add child at start
        insert         — add child at index
        remove         — remove child at index
        replace_child  — swap child at index

    Dunder methods:
        __len__        — child_count
        __iter__       — iterate over children
        __getitem__    — child at index (int or slice)
        __contains__   — identity check against children
        __bool__       — always True (a node exists)
        __repr__       — ClassName(child_count=N) or ClassName()
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

    # --- Reconstruction ---

    def with_children(self, *children: ChildT) -> Self:
        """Reconstruct this node with new children.

        Preserves node type. Subclasses with extra state
        should override to preserve that state.
        """
        if children == self._children:
            return self
        return type(self)(*children)

    # --- Modification (immutable — all return new nodes) ---

    def append(self, child: ChildT) -> Self:
        """New node with child added at the end."""
        return self.with_children(*self._children, child)

    def prepend(self, child: ChildT) -> Self:
        """New node with child added at the start."""
        return self.with_children(child, *self._children)

    def insert(self, index: int, child: ChildT) -> Self:
        """New node with child inserted at index."""
        children = list(self._children)
        children.insert(index, child)
        return self.with_children(*children)

    def remove(self, index: int) -> Self:
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

    def __len__(self) -> int:
        """Return child count."""
        return len(self._children)

    def __iter__(self) -> Iterator[ChildT]:
        """Iterate over direct children."""
        return iter(self._children)

    @overload
    def __getitem__(self, index: int) -> ChildT: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[ChildT, ...]: ...

    def __getitem__(self, index: int | slice) -> ChildT | tuple[ChildT, ...]:
        """Return child at index or slice of children."""
        return self._children[index]

    def __contains__(self, child: object) -> bool:
        """Check if child is in children by identity (``is``)."""
        return any(c is child for c in self._children)

    def __bool__(self) -> bool:
        """A node always exists (always True)."""
        return True

    def __repr__(self) -> str:
        """Return ClassName(child_count=N) or ClassName() for leaves."""
        name = type(self).__name__
        if self._children:
            return f"{name}(child_count={self.child_count})"
        return f"{name}()"
