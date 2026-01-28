"""Node -- immutable tree node with children management.

All operations return new nodes. Originals are never mutated.
This is the structural foundation -- no semantics attached.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterator


__all__ = [
    "Node",
]


class Node:
    """Immutable tree node with explicit children management.

    Access:
        children       -- direct child nodes (tuple)
        is_leaf        -- True if no children
        child_count    -- number of direct children

    Reconstruction:
        with_children  -- replace all children, preserving node identity

    Modification (all return new nodes):
        append         -- add child at end
        prepend        -- add child at start
        insert         -- add child at index
        remove         -- remove child at index
        replace_child  -- swap child at index

    Dunder methods:
        __len__        -- child_count
        __iter__       -- iterate over children
        __getitem__    -- child at index (int or slice)
        __contains__   -- identity check against children
        __bool__       -- always True (a node exists)
        __repr__       -- ClassName(child_count=N) or ClassName()
    """

    __slots__ = ()

    # --- Access ---

    @property
    def children(self) -> tuple[Node, ...]:
        """Direct child nodes. Default: leaf (empty)."""
        return ()

    @property
    def is_leaf(self) -> bool:
        """True if this node has no children."""
        return not self.children

    @property
    def child_count(self) -> int:
        """Number of direct children."""
        return len(self.children)

    # --- Reconstruction ---

    def with_children(self, *children: Node) -> Node:
        """Reconstruct this node with entirely new children.

        Preserves all non-child state (type, attributes, etc.).
        Leaf nodes return self when given no children.
        Branch nodes must override.
        """
        if not children and not self.children:
            return self
        msg = f"{type(self).__name__} must implement with_children"
        raise NotImplementedError(msg)

    # --- Modification (immutable -- all return new nodes) ---

    def append(self, child: Node) -> Node:
        """New node with child added at the end."""
        return self.with_children(*self.children, child)

    def prepend(self, child: Node) -> Node:
        """New node with child added at the start."""
        return self.with_children(child, *self.children)

    def insert(self, index: int, child: Node) -> Node:
        """New node with child inserted at index."""
        children = list(self.children)
        children.insert(index, child)
        return self.with_children(*children)

    def remove(self, index: int) -> Node:
        """New node with child at index removed."""
        children = list(self.children)
        del children[index]
        return self.with_children(*children)

    def replace_child(self, index: int, child: Node) -> Node:
        """New node with child at index replaced."""
        children = list(self.children)
        children[index] = child
        return self.with_children(*children)

    # --- Dunder methods ---

    def __len__(self) -> int:
        """Return child count."""
        return self.child_count

    def __iter__(self) -> Iterator[Node]:
        """Iterate over direct children."""
        return iter(self.children)

    def __getitem__(self, index: int | slice) -> Node | tuple[Node, ...]:
        """Return child at index or slice of children."""
        return self.children[index]

    def __contains__(self, child: object) -> bool:
        """Check if child is in children by identity (``is``)."""
        return any(c is child for c in self.children)

    def __bool__(self) -> bool:
        """A node always exists (always True)."""
        return True

    def __repr__(self) -> str:
        """Return ClassName(child_count=N) or ClassName() for leaves."""
        name = type(self).__name__
        if self.children:
            return f"{name}(child_count={self.child_count})"
        return f"{name}()"
