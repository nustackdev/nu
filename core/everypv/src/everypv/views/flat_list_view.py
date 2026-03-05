"""FlatListView — primitives-only list with length tracking, no nesting overhead.

Lightweight list view optimized for primitive values (int, float, str, bool,
bytes, None).  No observables, no nested containers, no child navigation.
Each element is a single ``put_child_primitive`` / ``get_child_primitive`` call.

Append is O(1) (one primitive write + one metadata write for length).
Iteration is a prefix scan over flat primitives only.
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import TYPE_CHECKING, ClassVar, cast

from pv.container import ContainerProtocol, ContainerStructure
from pv.types import Empty, Value
from pv.view import (
    ChildPrimitiveSetBase,
    MetadataBasedChildrenCountBase,
    UnsafePrimitiveOpsBase,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


__all__ = [
    "FlatListView",
]


class FlatListView(
    MetadataBasedChildrenCountBase,
    ChildPrimitiveSetBase,
    UnsafePrimitiveOpsBase,
    StdView,
):
    """Primitives-only list with O(1) append and length tracking.

    Stores only primitive values using integer keys (0, 1, 2, ...).
    Includes ``__len__`` via metadata.  No nested containers, no observables.

    Use when:
    - Elements are always primitives (str, int, etc.)
    - Append-heavy workload (key index, log, etc.)
    - You need fast ``len()`` and iteration without nesting overhead

    Example::

        >>> keys = FlatListView(container, registry)
        >>> keys.append("alice")
        >>> keys.append("bob")
        >>> print(len(keys))   # 2
        >>> print(keys[0])     # "alice"
        >>> print(list(keys))  # ["alice", "bob"]
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(14)
    PROTOCOL: ClassVar[ContainerProtocol] = (
        ContainerProtocol.INDEXED | ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
    )
    CONTAINER_CLS: ClassVar[type] = list

    @classmethod
    def is_address_static(cls, address: object) -> bool:
        """Positive int indices are passthrough."""
        return isinstance(address, int) and address >= 0

    def normalize_address(self, address: int) -> int:
        """Normalize index, handling negative indices."""
        length = len(self)
        if address < 0:
            address = length + address
        if address < 0 or address >= length:
            raise IndexError("list index out of range")
        return address

    # -- Read ---------------------------------------------------------------

    def __getitem__(self, address: int) -> Value:
        """Get primitive value at index."""
        normalized = self.normalize_address(address)
        value = self.container.get_child_primitive(normalized)
        if isinstance(value, Empty):
            raise IndexError("list index out of range")
        return value

    def __iter__(self) -> Generator[Value, None, None]:
        """Iterate over values via prefix scan (flat primitives only)."""
        for _k, v in self.container.iter_children(validate=False):
            yield cast("Value", v.primitive_value)

    def __contains__(self, obj: object) -> bool:
        for item in self:
            if item == obj:
                return True
        return False

    # -- Write --------------------------------------------------------------

    def append(self, value: Value) -> None:
        """Append a primitive value.  O(1): one primitive write + one metadata write."""
        self.ensure_created()
        index = len(self)
        self.container.put_child_primitive(index, value)
        self._set_length(index + 1)

    def __setitem__(self, address: int, value: Value) -> None:
        """Set primitive value at existing index."""
        normalized = self.normalize_address(address)
        self.container.put_child_primitive(normalized, value)

    def clear(self) -> None:
        """Remove all items."""
        self.ensure_created()
        self.container.clear_children(validate=False)
        self._set_length(0)

    # -- Bulk ---------------------------------------------------------------

    def store(self, value: Iterable[Value]) -> None:
        """Store list contents (replaces existing)."""
        self.ensure_created()
        self.clear()
        count = 0
        for item in value:
            self.container.put_child_primitive(count, item)
            count += 1
        self._set_length(count)

    def extend(self, values: Iterable[Value]) -> None:
        """Append multiple values."""
        self.ensure_created()
        index = len(self)
        for item in values:
            self.container.put_child_primitive(index, item)
            index += 1
        self._set_length(index)

    # -- Extract ------------------------------------------------------------

    def extract(self) -> list[Value]:
        """Extract all items as a plain list."""
        return list(self)

    def extract_range(self, start: int, stop: int) -> list[Value]:
        """Extract a range of items by index.  O(stop-start) individual reads."""
        length = len(self)
        start = max(0, start)
        stop = min(stop, length)
        result = []
        for i in range(start, stop):
            value = self.container.get_child_primitive(i)
            if not isinstance(value, Empty):
                result.append(value)
        return result


MutableSequence.register(FlatListView)
