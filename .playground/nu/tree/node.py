"""_Node - immutable generic tree node (internal).

All operations return new nodes. Originals are never mutated.
This is the structural foundation - no semantics attached.

Generic over ``ChildT`` so subclasses can narrow the children type:
``Nu(_Node["Nu"])`` makes all Nu methods return ``Nu``, not ``_Node``.

The only public member is ``children``. Every manipulation method is
underscore-prefixed: it's machinery for tree rewrites, not user surface.
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
    """Immutable tree node, generic over child type. Internal."""

    def __init__(self, *children: ChildT) -> None:
        self._children: tuple[ChildT, ...] = children

    @property
    def children(self) -> tuple[ChildT, ...]:
        """Direct child nodes. The only public surface."""
        return self._children

    # --- internal access ---

    @property
    def _is_leaf(self) -> bool:
        return not self._children

    @property
    def _child_count(self) -> int:
        return len(self._children)

    def _get_child(self, index: int) -> ChildT:
        return self._children[index]

    def _iter_children(self) -> Iterator[ChildT]:
        return iter(self._children)

    def _has_child(self, child: object) -> bool:
        return any(c is child for c in self._children)

    # --- internal reconstruction ---

    def _with_children(self, *children: ChildT) -> Self:
        """Shallow-copy with new children. Preserves instance state."""
        if children == self._children:
            return self
        clone = copy.copy(self)
        clone._children = children
        return clone

    # --- internal modification (all return new nodes) ---

    def _append_child(self, child: ChildT) -> Self:
        return self._with_children(*self._children, child)

    def _prepend_child(self, child: ChildT) -> Self:
        return self._with_children(child, *self._children)

    def _insert_child(self, index: int, child: ChildT) -> Self:
        children = list(self._children)
        children.insert(index, child)
        return self._with_children(*children)

    def _remove_child(self, index: int) -> Self:
        children = list(self._children)
        del children[index]
        return self._with_children(*children)

    def _replace_child(self, index: int, child: ChildT) -> Self:
        children = list(self._children)
        children[index] = child
        return self._with_children(*children)

    # --- dunder methods ---

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        name = type(self).__name__
        if self._children:
            return f"{name}(child_count={len(self._children)})"
        return f"{name}()"
