"""ByteArrayView - ByteArray-like view over container."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, ClassVar, cast

from pv.container import ContainerProtocol, ContainerStructure
from pv.typing import is_empty
from pv.view import (
    ChildObservableBase,
    MetadataBasedChildrenCountBase,
    ObservableBase,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from pv.typing.view import (
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

        normalized = self.normalize_address(address)
        self.container.put_child_primitive(normalized, value)

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
        self.container.put_child_primitive(index, value)

    def clear(self) -> None:
        """Remove all bytes."""
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
        self.clear()

        for index, byte in enumerate(value):
            self.container.put_child_primitive(index, byte)


if TYPE_CHECKING:
    _subscriptable: type[Subscriptable[int, int]] = ByteArrayView
    _convertible: type[Convertible[bytearray]] = ByteArrayView
    _initializable: type[Initializable[Iterable[int]]] = ByteArrayView
    _assignable: type[Assignable[int, int]] = ByteArrayView
    _watchable: type[ObservableBase] = ByteArrayView
    _watchable_children: type[ChildObservableBase] = ByteArrayView
