"""TupleView - Tuple-like view over container (immutable sequence)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

from pv.container import (
    Container,
    ContainerNotFoundError,
    ContainerProtocol,
    ContainerStructure,
)
from pv.loc import key as key_
from pv.view import (
    ChildNavigationBase,
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildPrimitiveSetBase,
    MetadataBasedChildrenCountBase,
    UnsafePrimitiveOpsBase,
    View,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from pv.collections import SequenceView
    from pv.traits import (
        Containable,
        Convertible,
        Initializable,
        Nestable,
        Sizeable,
        Subscriptable,
    )
    from pv.types import Empty

__all__ = ["TupleView"]


class TupleView(
    MetadataBasedChildrenCountBase,
    ChildNavigationBase[int],
    ChildNestedGetBase,
    ChildNestedSetBase,
    ChildPrimitiveSetBase,
    UnsafePrimitiveOpsBase,
    StdView,
):
    """Tuple-like view over container (immutable sequence).

    Provides read-only tuple interface using integer keys:
    - __getitem__, __len__, __iter__
    - count(), index()

    Type Parameters:
        V: Type of values (default: Value)

    Example:
        >>> coords: TupleView[int] = TupleView(container, registry)
        >>> # Must be initialized via store()
        >>> coords.store((10, 20, 30))
        >>> print(coords[0])  # 10
        >>> print(len(coords))  # 3
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(3)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.INDEXED | ContainerProtocol.SIZED
    CONTAINER_CLS: ClassVar[type] = tuple

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
            raise IndexError("tuple index out of range")

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
        normalized = self.normalize_address(address)
        try:
            return self._get_child_value(normalized)
        except ContainerNotFoundError as e:
            raise IndexError("tuple index out of range") from e

    def __iter__(self) -> Generator[object, None, None]:
        """Iterate over items.

        Yields:
            Items in order
        """
        for i in range(len(self)):
            yield self[i]

    def __contains__(self, obj: object) -> bool:
        """Check if value exists in tuple.

        Args:
            obj: Value to check for

        Returns:
            True if value exists in tuple
        """
        for item in self:
            if item == obj:
                return True
        return False

    def __reversed__(self) -> Generator[object, None, None]:
        """Iterate in reverse order.

        Yields:
            Items in reverse order
        """
        for i in range(len(self) - 1, -1, -1):
            yield self[i]

    def index(self, value: object) -> int:
        """Find index of first occurrence of value.

        Args:
            value: Value to find

        Returns:
            Index of first occurrence

        Raises:
            ValueError: If value not found
        """
        for i, item in enumerate(self):
            if item == value:
                return i
        raise ValueError(f"{value!r} is not in tuple")

    def count(self, value: object) -> int:
        """Count occurrences of value.

        Args:
            value: Value to count

        Returns:
            Number of occurrences
        """
        return sum(1 for item in self if item == value)

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> tuple[object, ...]:
        """Extract all items as tuple.

        Returns:
            Tuple of all items in order
        """
        return tuple(self)

    def store(self, value: Iterable[object]) -> None:
        """Store tuple contents.

        Args:
            value: Sequence to store
            replace: If True, clear existing content first
        """
        self.ensure_created()
        self.container.clear_children()

        count = 0
        for index, item in enumerate(value):
            self._set_child_value(index, item)
            count += 1

        # Set final length metadata
        self._set_length(count)

    def open_child[ViewT: View](self, address: int, view: type[ViewT]) -> ViewT:
        """Open child view at index.

        Pure navigation — does not write to storage.

        Args:
            address: Child container index
            view: View class for child

        Returns:
            View instance for child container
        """
        normalized = self.normalize_address(address)
        child_site = key_.join_segment(self.container.site, normalized)
        child_container = Container(ctx=self.container.ctx, site=child_site)
        return view(child_container, self.registry)


Sequence.register(TupleView)


if TYPE_CHECKING:
    # Verify protocol implementations
    _subscriptable: type[Subscriptable[int, object]] = TupleView
    _convertible: type[Convertible[object]] = TupleView
    _initializable: type[Initializable[Iterable[object]]] = TupleView
    _nestable: type[Nestable[int]] = TupleView
    _containable: type[Containable[object]] = TupleView
    _sizeable: type[Sizeable] = TupleView
    _sequence: type[SequenceView[object]] = TupleView
