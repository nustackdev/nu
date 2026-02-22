"""ByteArrayView - ByteArray-like view over container."""

from __future__ import annotations

from collections.abc import Generator, MutableSequence
from typing import TYPE_CHECKING, ClassVar, cast

from pv.container import ContainerProtocol, ContainerStructure
from pv.types import is_empty
from pv.view import (
    ChildObservableBase,
    ChildPrimitiveSetBase,
    MetadataBasedChildrenCountBase,
    ObservableBase,
    UnsafePrimitiveOpsBase,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from pv.traits import (
        Assignable,
        Convertible,
        Initializable,
        Subscriptable,
    )


__all__ = ["ByteArrayView"]


class ByteArrayView(
    ObservableBase,
    ChildObservableBase[int],
    MetadataBasedChildrenCountBase,
    ChildPrimitiveSetBase,
    UnsafePrimitiveOpsBase,
    StdView,
):
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

    @classmethod
    def is_address_static(cls, address: object) -> bool:
        """Positive int indices are passthrough; negative need len() lookup."""
        return isinstance(address, int) and address >= 0

    def normalize_address(self, address: int) -> int:
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
            raise IndexError("bytearray address (index) out of range")

        return address

    def __getitem__(self, address: int) -> int:
        """Get byte at index.

        Args:
            address: Index (supports negative)

        Returns:
            Byte value (0-255)

        Raises:
            IndexError: If index out of bounds
        """
        normalized = self.normalize_address(address)
        value = self.container.get_child_primitive(normalized)
        if is_empty(value):
            raise IndexError("bytearray index out of range")
        return cast("int", value)

    def __setitem__(self, address: int, value: int) -> None:
        """Set byte at index.

        Args:
            address: Index (supports negative)
            value: Byte value (0-255)

        Raises:
            IndexError: If index out of bounds
            ValueError: If value not in range 0-255
        """
        if not isinstance(value, int) or not 0 <= value <= 255:
            raise ValueError("byte must be in range(0, 256)")

        self.ensure_created()
        normalized = self.normalize_address(address)
        self.container.put_child_primitive(normalized, value)

    def __iter__(self) -> Generator[int, None, None]:
        """Iterate over bytes.

        Yields:
            Byte values (0-255)
        """
        for i in range(len(self)):
            yield self[i]

    def __contains__(self, value: object) -> bool:
        """Check if byte value exists."""
        for byte in self:
            if byte == value:
                return True
        return False

    def __reversed__(self) -> Generator[int, None, None]:
        """Iterate over bytes in reverse."""
        for i in range(len(self) - 1, -1, -1):
            yield self[i]

    def __delitem__(self, address: int) -> None:
        """Delete byte at index. Not supported — requires element shifting."""
        raise NotImplementedError("ByteArrayView does not support item deletion")

    def append(self, value: int) -> None:
        """Append byte to end.

        Args:
            value: Byte value (0-255)

        Raises:
            ValueError: If value not in range 0-255
        """
        if not isinstance(value, int) or not 0 <= value <= 255:
            raise ValueError("byte must be in range(0, 256)")

        self.ensure_created()
        index = len(self)
        self.container.put_child_primitive(index, value)

    def insert(self, index: int, value: int) -> None:
        """Insert byte at index. Not supported — requires element shifting."""
        raise NotImplementedError("ByteArrayView does not support insert")

    def pop(self, index: int = -1) -> int:
        """Remove and return byte at index. Not supported — requires element shifting."""
        raise NotImplementedError("ByteArrayView does not support pop")

    def extend(self, values: Iterable[int]) -> None:
        """Extend with bytes from iterable."""
        for value in values:
            self.append(value)

    def remove(self, value: int) -> None:
        """Remove first occurrence of byte value. Not supported — requires element shifting."""
        raise NotImplementedError("ByteArrayView does not support remove")

    def index(self, value: int) -> int:
        """Find index of first occurrence of byte value.

        Raises:
            ValueError: If value not found
        """
        for i, byte in enumerate(self):
            if byte == value:
                return i
        raise ValueError(f"{value!r} is not in bytearray")

    def count(self, value: int) -> int:
        """Count occurrences of byte value."""
        return sum(1 for byte in self if byte == value)

    def clear(self) -> None:
        """Remove all bytes."""
        self.ensure_created()
        self.container.clear_children()

    def extract(self) -> bytearray:
        """Extract all bytes as bytearray.

        Returns:
            Bytearray of all bytes
        """
        return bytearray(self)

    def store(self, value: Iterable[int]) -> None:
        """Store bytearray contents.

        Args:
            value: Bytes or bytearray to store
            replace: If True, clear existing content first
        """
        self.ensure_created()
        self.clear()

        for index, byte in enumerate(value):
            self.container.put_child_primitive(index, byte)


MutableSequence.register(ByteArrayView)


if TYPE_CHECKING:
    _subscriptable: type[Subscriptable[int, int]] = ByteArrayView
    _convertible: type[Convertible[bytearray]] = ByteArrayView
    _initializable: type[Initializable[Iterable[int]]] = ByteArrayView
    _assignable: type[Assignable[int, int]] = ByteArrayView
    _watchable: type[ObservableBase] = ByteArrayView
    _watchable_children: type[ChildObservableBase] = ByteArrayView
