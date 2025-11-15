"""ListView - List-like view over container."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from redwood.tree import (
    ContainerProtocol,
    ContainerStructure,
    NodeType,
    PathNotFoundError,
)
from redwood.types import Empty, Value, cast_value
from redwood.view import (
    ChildNavigationMixin,
    ChildNestedGetMixin,
    ChildNestedSetMixin,
    MetadataBasedChildrenCountMixin,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from redwood.types import (
        Appendable,
        Assignable,
        Clearable,
        Containable,
        Convertible,
        Deletable,
        Initializable,
        MutableSequence,
        Nestable,
        Sizeable,
        Subscriptable,
    )


__all__ = ["ListView"]


class ListView(
    MetadataBasedChildrenCountMixin,
    ChildNavigationMixin[int],
    ChildNestedGetMixin,
    ChildNestedSetMixin,
    StdView,
):
    """List-like view over container.

    Provides familiar list interface using integer keys:
    - __getitem__, __setitem__, __delitem__
    - append(), pop(), insert()
    - Index-based operations

    Type Parameters:
        V: Type of values (default: Value)

    Example:
        >>> tasks: ListView[str] = ListView(container, registry)
        >>> tasks.append("Buy groceries")
        >>> tasks.append("Write code")
        >>> print(tasks[0])  # "Buy groceries"
        >>> print(len(tasks))  # 2
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(2)
    PROTOCOL: ClassVar[ContainerProtocol] = (
        ContainerProtocol.INDEXED | ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
    )
    CONTAINER_CLS: ClassVar[type] = list

    def address_normalization(self, address: int) -> int:
        """Normalize index, handling negative indices.

        Args:
            address: Index to normalize

        Returns:
            Normalized positive index

        Raises:
            IndexError: If index out of bounds
        """
        length = len(self)

        if address < 0:
            address = length + address

        if address < 0 or address >= length:
            raise IndexError("list index out of range")

        return address

    def __getitem__(self, address: int) -> object | Empty:
        """Get item at index.

        Args:
            address: Index (supports negative)

        Returns:
            Value at index

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self.address_normalization(address)
        try:
            return self._get_child_value(normalized)
        except PathNotFoundError as e:
            raise IndexError("list index out of bounds") from e

    def __setitem__(self, address: int, value: object) -> None:
        """Set item at index.

        Args:
            address: Index (supports negative)
            value: Value to store

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self.address_normalization(address)
        self._set_child_value(normalized, value)

    def __delitem__(self, address: int) -> None:
        """Delete item at index and shift remaining items.

        Args:
            address: Index (supports negative)

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self.address_normalization(address)
        length = len(self)

        # Delete the item
        self.container.delete_child(normalized)

        # Shift remaining items down
        for i in range(normalized + 1, length):
            child_type = self.container.get_child_type(i)
            if child_type == NodeType.PRIMITIVE:
                value = self.container.get_child_primitive(i)
                self.container.set_child_primitive(i - 1, cast_value(value))
                self.container.delete_child(i)
            elif child_type == NodeType.CONTAINER:
                # Container child - needs more complex move logic
                raise NotImplementedError(
                    "Deleting list items with container children not yet supported"
                )

        # Update length metadata
        self._set_length(length - 1)

    def __iter__(self) -> Generator[Value, None, None]:
        """Iterate over items.

        Yields:
            Items in order
        """
        for k, v in self.container.list_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield cast_value(v.primitive_value)
            elif v.node_type == NodeType.CONTAINER:
                yield cast_value(self[int(k)])

    def __contains__(self, obj: object) -> bool:
        """Check if value exists in list.

        Args:
            obj: Value to check for

        Returns:
            True if value exists in list
        """
        for item in self:
            if item == obj:
                return True
        return False

    def append(self, value: object) -> None:
        """Append value to end.

        Args:
            value: Value to append
        """
        index = len(self)
        self._set_child_value(index, value)
        # Update length metadata
        self._set_length(index + 1)

    def pop(self, address: int = -1) -> object | Empty:
        """Remove and return item at index.

        Args:
            address: Index to remove (default: last)

        Returns:
            Removed value

        Raises:
            IndexError: If list empty or index out of bounds
        """
        if len(self) == 0:
            raise IndexError("pop from empty list")

        value = self[address]
        del self[address]
        return value

    def insert(self, address: int, value: object) -> None:
        """Insert value at index, shifting later items.

        Args:
            address: Index to insert at
            value: Value to insert
        """
        length = len(self)

        # Clamp index to valid range
        if address < 0:
            address = max(0, length + address)
        else:
            address = min(address, length)

        # Shift items up
        for i in range(length - 1, address - 1, -1):
            child_type = self.container.get_child_type(i)
            if child_type == NodeType.PRIMITIVE:
                child_value = self.container.get_child_primitive(i)
                self.container.set_child_primitive(i + 1, cast_value(child_value))
            elif child_type == NodeType.CONTAINER:
                raise NotImplementedError(
                    "Inserting into list with container children not yet supported"
                )

        # Insert new value
        self._set_child_value(address, value)
        # Update length metadata
        self._set_length(length + 1)

    def clear(self) -> None:
        """Remove all items."""
        self.container.clear_children()
        # Reset length metadata
        self._set_length(0)

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> list[Value]:
        """Extract all items as list.

        Returns:
            List of all items in order
        """
        return list(self)

    def store(self, value: Iterable[object]) -> None:
        """Store list contents.

        Args:
            value: Sequence to store
            replace: If True, clear existing content first
        """
        self.clear()

        # Batch append and update length once at end
        count = 0
        for item in value:
            self._set_child_value(count, item)
            count += 1

        # Set final length metadata
        self._set_length(count)


if TYPE_CHECKING:
    # Verify protocol implementations
    _subscriptable: type[Subscriptable[int, object]] = ListView
    _convertible: type[Convertible[object]] = ListView
    _initializable: type[Initializable[Iterable[object]]] = ListView
    _assignable: type[Assignable[int, object]] = ListView
    _nestable: type[Nestable[int]] = ListView
    _containable: type[Containable[object]] = ListView
    _sizeable: type[Sizeable] = ListView
    _deletable: type[Deletable[int]] = ListView
    _clearable: type[Clearable] = ListView
    _appendable: type[Appendable[object]] = ListView
    _mutable_sequence: type[MutableSequence[object]] = ListView
