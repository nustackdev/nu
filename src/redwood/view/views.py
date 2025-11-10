"""Built-in views for common Python data structures.

This module provides view implementations for standard Python types,
all built on the Container API. Each view provides a familiar interface
while delegating storage operations to Layer 2.

Available views:
    - DictView: Mutable mapping (dict)
    - ListView: Mutable sequence (list)
    - TupleView: Immutable sequence (tuple)
    - SetView: Mutable set (set)
    - FrozenSetView: Immutable set (frozenset)
    - ByteArrayView: Mutable byte sequence (bytearray)

Each view implements:
    - Native Python protocols (__getitem__, __iter__, etc.)
    - Convertible protocol (extract() method)
    - Initializable protocol (store() method)
    - Nestable protocol (open_view() method) where appropriate

Example:
    >>> from redwood.view import ViewRegistry
    >>> from redwood.view.views import DictView
    >>> from redwood.tree import Container, ContainerStructure, ContainerProtocol
    >>> registry = ViewRegistry()
    >>> registry.register_builtin_views()
    >>> with storage.transaction() as tx:
    ...     container = Container.create(
    ...         path=("users",),
    ...         ctx=tx,
    ...         structure=DictView.STRUCTURE,
    ...         protocol=DictView.PROTOCOL,
    ...     )
    ...
    ...     users = DictView(container, registry)
    ...     users["alice"] = {"name": "Alice", "age": 30}
    ...     users["bob"] = {"name": "Bob", "tags": ["python", "ai"]}
    ...
    ...     # Nested structures auto-populate
    ...     alice = users["alice"]  # Returns: {"name": "Alice", "age": 30}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from redwood.abc import EMPTY, Empty, KeyComponent, Value, cast_value, is_empty
from redwood.tree import (
    Container,
    ContainerProtocol,
    ContainerStructure,
    NodeType,
    PathNotFoundError,
    join_component,
)

from .view import View


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Mapping, Sequence

__all__ = [
    "ByteArrayView",
    "DictView",
    "FrozenSetView",
    "ListView",
    "SetView",
    "TupleView",
]

# =============================================================================
# DICTVIEW
# =============================================================================


class DictView(View):
    """Dict-like view over container.

    Provides familiar dict interface while delegating to Container:
    - __getitem__, __setitem__, __delitem__
    - keys(), values(), items()
    - get(), pop(), clear()

    Example:
        >>> users = DictView(container, registry)
        >>> users["alice"] = {"name": "Alice", "tags": ["python"]}
        >>> alice = users["alice"]
        >>> print(list(users.keys()))
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(1)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MAPPING | ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type] = dict

    def __getitem__(self, key: KeyComponent) -> Value | Empty:
        """Get value for key.

        Args:
            key: Key to retrieve

        Returns:
            Value (auto-extracted if container)

        Raises:
            KeyError: If key not found
        """
        try:
            return self._get_child_value(key)
        except PathNotFoundError as e:
            raise KeyError(key) from e

    def __setitem__(self, key: KeyComponent, value: Value) -> None:
        """Set value for key.

        Args:
            key: Key to set
            value: Value to store (auto-populated if container type)
        """
        self._set_child_value(key, value)

    def __delitem__(self, key: KeyComponent) -> None:
        """Delete key.

        Args:
            key: Key to delete

        Raises:
            KeyError: If key not found
        """
        deleted = self.container.delete_child(key)
        if not deleted:
            raise KeyError(key)

    def __contains__(self, key: KeyComponent) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        return self.container.has_child(key)

    def __len__(self) -> int:
        """Get number of keys.

        Returns:
            Number of keys
        """
        return self.container.count_children()

    def keys(self) -> Generator[KeyComponent, None, None]:
        """Get all keys.

        Yields:
            Keys in storage order
        """
        yield from self.container.list_child_keys()

    def values(self) -> Generator[Value, None, None]:
        """Get all values.

        Yields:
            Values in storage order
        """
        for k, v in self.container.list_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield cast_value(v.primitive_value)
            elif v.node_type == NodeType.CONTAINER:
                yield cast_value(self[k])

    def items(self) -> Generator[tuple[KeyComponent, Value], None, None]:
        """Get all key-value pairs.

        Yields:
            (key, value) tuples in storage order
        """
        for k, v in self.container.list_children():
            if v.node_type == NodeType.PRIMITIVE:
                yield k, cast_value(v.primitive_value)
            elif v.node_type == NodeType.CONTAINER:
                yield k, cast_value(self[k])

    def get(self, key: KeyComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """Get value with default fallback.

        Args:
            key: Key to retrieve
            default: Default if key not found

        Returns:
            Value or default
        """
        try:
            return self._get_child_value(key)
        except Exception:
            return default

    def pop(self, key: KeyComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """Remove and return value.

        Args:
            key: Key to remove
            default: Default if key not found

        Returns:
            Removed value or default

        Raises:
            KeyError: If key not found and no default
        """
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            if is_empty(default):
                raise
            return default

    def clear(self) -> None:
        """Remove all items."""
        self.container.clear_children()

    def update(self, other: Mapping[KeyComponent, Value] | None = None, **kwargs: Value) -> None:
        """Update from dict or kwargs.

        Args:
            other: Dict to update from
            **kwargs: Additional key-value pairs
        """
        if other:
            for key, value in other.items():
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> dict[KeyComponent, Value]:
        """Extract all items as dict.

        Returns:
            Dict of all key-value pairs
        """
        return dict(self.items())

    def store(self, value: Mapping, /, replace: bool = False) -> None:
        """Store dict contents.

        Args:
            value: Mapping to store
            replace: If True, clear existing content first
        """
        if replace:
            self.clear()

        for key, val in value.items():
            self[key] = val

    def open_view[ViewT: View](self, key: KeyComponent, child_view: type[ViewT]) -> ViewT:
        """Open child view.

        Args:
            key: Child container key
            child_view: View class for child

        Returns:
            View instance for child container
        """
        child_container = Container.create(
            join_component(self.container.path, key),
            self.container.ctx,
            child_view.get_structure(),
            child_view.get_protocol(),
        )
        return child_view(child_container, self.registry)


# =============================================================================
# LISTVIEW
# =============================================================================


class ListView(View):
    """List-like view over container.

    Provides familiar list interface using integer keys:
    - __getitem__, __setitem__, __delitem__
    - append(), pop(), insert()
    - Index-based operations

    Example:
        >>> tasks = ListView(container, registry)
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

    def _normalize_index(self, index: int) -> int:
        """Normalize index, handling negative indices.

        Args:
            index: Index to normalize

        Returns:
            Normalized positive index

        Raises:
            IndexError: If index out of bounds
        """
        length = len(self)

        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError("list index out of range")

        return index

    def __getitem__(self, index: int) -> Value | Empty:
        """Get item at index.

        Args:
            index: Index (supports negative)

        Returns:
            Value at index

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self._normalize_index(index)
        try:
            return self._get_child_value(normalized)
        except PathNotFoundError as e:
            raise IndexError("list index out of range") from e

    def __setitem__(self, index: int, value: Value) -> None:
        """Set item at index.

        Args:
            index: Index (supports negative)
            value: Value to store

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self._normalize_index(index)
        self._set_child_value(normalized, value)

    def __delitem__(self, index: int) -> None:
        """Delete item at index and shift remaining items.

        Args:
            index: Index (supports negative)

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self._normalize_index(index)
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

    def __len__(self) -> int:
        """Get number of items.

        Returns:
            Number of items
        """
        return self.container.count_children()

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

    def append(self, value: Value) -> None:
        """Append value to end.

        Args:
            value: Value to append
        """
        index = len(self)
        self._set_child_value(index, value)

    def pop(self, index: int = -1) -> Value | Empty:
        """Remove and return item at index.

        Args:
            index: Index to remove (default: last)

        Returns:
            Removed value

        Raises:
            IndexError: If list empty or index out of bounds
        """
        if len(self) == 0:
            raise IndexError("pop from empty list")

        value = self[index]
        del self[index]
        return value

    def insert(self, index: int, value: Value) -> None:
        """Insert value at index, shifting later items.

        Args:
            index: Index to insert at
            value: Value to insert
        """
        length = len(self)

        # Clamp index to valid range
        if index < 0:
            index = max(0, length + index)
        else:
            index = min(index, length)

        # Shift items up
        for i in range(length - 1, index - 1, -1):
            child_type = self.container.get_child_type(i)
            if child_type == NodeType.PRIMITIVE:
                child_value = self.container.get_child_primitive(i)
                self.container.set_child_primitive(i + 1, cast_value(child_value))
            elif child_type == NodeType.CONTAINER:
                raise NotImplementedError(
                    "Inserting into list with container children not yet supported"
                )

        # Insert new value
        self._set_child_value(index, value)

    def clear(self) -> None:
        """Remove all items."""
        self.container.clear_children()

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> list[Value]:
        """Extract all items as list.

        Returns:
            List of all items in order
        """
        return list(self)

    def store(self, value: Sequence, /, replace: bool = False) -> None:
        """Store list contents.

        Args:
            value: Sequence to store
            replace: If True, clear existing content first
        """
        if replace:
            self.clear()

        for item in value:
            self.append(item)

    def open_view[ViewT: View](self, index: int, child_view: type[ViewT]) -> ViewT:
        """Open child view at index.

        Args:
            index: Child container index
            child_view: View class for child

        Returns:
            View instance for child container
        """
        normalized = self._normalize_index(index)
        child_container = Container.create(
            join_component(self.container.path, normalized),
            self.container.ctx,
            child_view.get_structure(),
            child_view.get_protocol(),
        )
        return child_view(child_container, self.registry)


# =============================================================================
# TUPLEVIEW
# =============================================================================


class TupleView(View):
    """Tuple-like view over container (immutable sequence).

    Provides read-only tuple interface using integer keys:
    - __getitem__, __len__, __iter__
    - count(), index()

    Example:
        >>> coords = TupleView(container, registry)
        >>> # Must be initialized via store()
        >>> coords.store((10, 20, 30))
        >>> print(coords[0])  # 10
        >>> print(len(coords))  # 3
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(3)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.INDEXED | ContainerProtocol.SIZED
    CONTAINER_CLS: ClassVar[type] = tuple

    def _normalize_index(self, index: int) -> int:
        """Normalize index, handling negative indices.

        Args:
            index: Index to normalize

        Returns:
            Normalized positive index

        Raises:
            IndexError: If index out of bounds
        """
        length = len(self)

        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError("tuple index out of range")

        return index

    def __getitem__(self, index: int) -> Value | Empty:
        """Get item at index.

        Args:
            index: Index (supports negative)

        Returns:
            Value at index

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self._normalize_index(index)
        try:
            return self._get_child_value(normalized)
        except PathNotFoundError as e:
            raise IndexError("tuple index out of range") from e

    def __len__(self) -> int:
        """Get number of items.

        Returns:
            Number of items
        """
        return self.container.count_children()

    def __iter__(self) -> Generator[Value, None, None]:
        """Iterate over items.

        Yields:
            Items in order
        """
        for i in range(len(self)):
            yield cast_value(self[i])

    def count(self, value: Value) -> int:
        """Count occurrences of value.

        Args:
            value: Value to count

        Returns:
            Number of occurrences
        """
        return sum(1 for item in self if item == value)

    def index(self, value: Value, start: int = 0, stop: int | None = None) -> int:
        """Find first index of value.

        Args:
            value: Value to find
            start: Start index
            stop: Stop index

        Returns:
            Index of first occurrence

        Raises:
            ValueError: If value not found
        """
        if stop is None:
            stop = len(self)

        for i in range(start, stop):
            if self[i] == value:
                return i

        raise ValueError(f"{value!r} is not in tuple")

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> tuple[Value, ...]:
        """Extract all items as tuple.

        Returns:
            Tuple of all items in order
        """
        return tuple(self)

    def store(self, value: Sequence, /, replace: bool = False) -> None:
        """Store tuple contents.

        Args:
            value: Sequence to store
            replace: If True, clear existing content first
        """
        if replace:
            self.container.clear_children()

        for index, item in enumerate(value):
            self._set_child_value(index, item)

    def open_view[ViewT: View](self, index: int, child_view: type[ViewT]) -> ViewT:
        """Open child view at index.

        Args:
            index: Child container index
            child_view: View class for child

        Returns:
            View instance for child container
        """
        normalized = self._normalize_index(index)
        child_container = Container.create(
            join_component(self.container.path, normalized),
            self.container.ctx,
            child_view.get_structure(),
            child_view.get_protocol(),
        )
        return child_view(child_container, self.registry)


# =============================================================================
# SETVIEW
# =============================================================================


class SetView(View):
    """Set-like view over container.

    Provides set interface using values as keys:
    - add(), remove(), discard()
    - __contains__, __len__, __iter__

    Implementation:
    - Uses string representation of values as keys
    - Stores actual values for extraction

    Example:
        >>> tags = SetView(container, registry)
        >>> tags.add("python")
        >>> tags.add("ai")
        >>> print("python" in tags)  # True
        >>> print(len(tags))  # 2
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(4)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.SET | ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type] = set

    def _make_key(self, value: Value) -> KeyComponent:
        """Convert value to storage key.

        Args:
            value: Value to store in set

        Returns:
            Key for storage
        """
        return str(value)

    def add(self, value: Value) -> None:
        """Add value to set.

        Args:
            value: Value to add
        """
        key = self._make_key(value)
        self.container.set_child_primitive(key, value)

    def remove(self, value: Value) -> None:
        """Remove value from set.

        Args:
            value: Value to remove

        Raises:
            KeyError: If value not in set
        """
        key = self._make_key(value)
        deleted = self.container.delete_child(key)
        if not deleted:
            raise KeyError(value)

    def discard(self, value: Value) -> None:
        """Remove value from set if present.

        Args:
            value: Value to remove
        """
        key = self._make_key(value)
        self.container.delete_child(key)

    def __contains__(self, value: Value) -> bool:
        """Check if value in set.

        Args:
            value: Value to check

        Returns:
            True if value in set
        """
        key = self._make_key(value)
        return self.container.has_child(key)

    def __len__(self) -> int:
        """Get number of values.

        Returns:
            Number of values
        """
        return self.container.count_children()

    def __iter__(self) -> Generator[Value, None, None]:
        """Iterate over values.

        Yields:
            Values in set
        """
        for key in self.container.list_child_keys():
            stored_value = self.container.get_child_primitive(key)
            if not is_empty(stored_value):
                yield cast_value(stored_value)

    def clear(self) -> None:
        """Remove all values."""
        self.container.clear_children()

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> set[Value]:
        """Extract all values as set.

        Returns:
            Set of all values
        """
        return set(self)

    def store(self, value: Iterable, /, replace: bool = False) -> None:
        """Store set contents.

        Args:
            value: Iterable to store
            replace: If True, clear existing content first
        """
        if replace:
            self.clear()

        for item in value:
            self.add(item)


# =============================================================================
# FROZENSETVIEW
# =============================================================================


class FrozenSetView(View):
    """Frozenset-like view over container (immutable set).

    Provides read-only set interface:
    - __contains__, __len__, __iter__

    Example:
        >>> perms = FrozenSetView(container, registry)
        >>> # Must be initialized via store()
        >>> perms.store({"read", "write", "execute"})
        >>> print("read" in perms)  # True
        >>> print(len(perms))  # 3
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(5)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.SET
    CONTAINER_CLS: ClassVar[type] = frozenset

    def _make_key(self, value: Value) -> KeyComponent:
        """Convert value to storage key.

        Args:
            value: Value to store in set

        Returns:
            Key for storage
        """
        return str(value)

    def __contains__(self, value: Value) -> bool:
        """Check if value in set.

        Args:
            value: Value to check

        Returns:
            True if value in set
        """
        key = self._make_key(value)
        return self.container.has_child(key)

    def __len__(self) -> int:
        """Get number of values.

        Returns:
            Number of values
        """
        return self.container.count_children()

    def __iter__(self) -> Generator[Value, None, None]:
        """Iterate over values.

        Yields:
            Values in set
        """
        for key in self.container.list_child_keys():
            stored_value = self.container.get_child_primitive(key)
            if not is_empty(stored_value):
                yield cast_value(stored_value)

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> frozenset[Value]:
        """Extract all values as frozenset.

        Returns:
            Frozenset of all values
        """
        return frozenset(self)

    def store(self, value: Iterable, /, replace: bool = False) -> None:
        """Store frozenset contents.

        Args:
            value: Iterable to store
            replace: If True, clear existing content first
        """
        if replace:
            self.container.clear_children()

        for item in value:
            key = self._make_key(item)
            self.container.set_child_primitive(key, item)


# =============================================================================
# BYTEARRAYVIEW
# =============================================================================


class ByteArrayView(View):
    """ByteArray-like view over container.

    Stores bytes as individual integer children for efficient access.
    Provides bytearray interface with indexing and mutation.

    Example:
        >>> data = ByteArrayView(container, registry)
        >>> data.store(bytearray(b"hello"))
        >>> print(data[0])  # 104 (ord('h'))
        >>> data[0] = 72
        >>> print(data.extract())  # bytearray(b'Hello')
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(6)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.MUTABLE | ContainerProtocol.INDEXED
    CONTAINER_CLS: ClassVar[type] = bytearray

    def _normalize_index(self, index: int) -> int:
        """Normalize index, handling negative indices.

        Args:
            index: Index to normalize

        Returns:
            Normalized positive index

        Raises:
            IndexError: If index out of bounds
        """
        length = len(self)

        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError("bytearray index out of range")

        return index

    def __getitem__(self, index: int) -> int:
        """Get byte at index.

        Args:
            index: Index (supports negative)

        Returns:
            Byte value (0-255)

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self._normalize_index(index)
        value = self.container.get_child_primitive(normalized)
        if is_empty(value):
            raise IndexError("bytearray index out of range")
        return cast("int", value)

    def __setitem__(self, index: int, value: int) -> None:
        """Set byte at index.

        Args:
            index: Index (supports negative)
            value: Byte value (0-255)

        Raises:
            IndexError: If index out of bounds
            ValueError: If value not in range 0-255
        """
        if not isinstance(value, int) or not 0 <= value <= 255:
            raise ValueError("byte must be in range(0, 256)")

        normalized = self._normalize_index(index)
        self.container.set_child_primitive(normalized, value)

    def __len__(self) -> int:
        """Get number of bytes.

        Returns:
            Number of bytes
        """
        return self.container.count_children()

    def __iter__(self) -> Generator[int, None, None]:
        """Iterate over bytes.

        Yields:
            Byte values (0-255)
        """
        for i in range(len(self)):
            yield self[i]

    def append(self, value: int) -> None:
        """Append byte to end.

        Args:
            value: Byte value (0-255)

        Raises:
            ValueError: If value not in range 0-255
        """
        if not isinstance(value, int) or not 0 <= value <= 255:
            raise ValueError("byte must be in range(0, 256)")

        index = len(self)
        self.container.set_child_primitive(index, value)

    def clear(self) -> None:
        """Remove all bytes."""
        self.container.clear_children()

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> bytearray:
        """Extract all bytes as bytearray.

        Returns:
            Bytearray of all bytes
        """
        return bytearray(self)

    def store(self, value: bytes | bytearray, /, replace: bool = False) -> None:
        """Store bytearray contents.

        Args:
            value: Bytes or bytearray to store
            replace: If True, clear existing content first
        """
        if replace:
            self.clear()

        for index, byte in enumerate(value):
            self.container.set_child_primitive(index, byte)


__all__ = [
    "ByteArrayView",
    "DictView",
    "FrozenSetView",
    "ListView",
    "SetView",
    "TupleView",
]
