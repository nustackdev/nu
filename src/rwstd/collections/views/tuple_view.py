"""TupleView - Tuple-like view over container (immutable sequence)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from redwood.loc import key as key_
from redwood.tree import (
    Container,
    ContainerProtocol,
    ContainerStructure,
    PathNotFoundError,
)
from redwood.types import Empty, cast_value
from redwood.view import View

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from redwood.types import (
        Containable,
        Convertible,
        Initializable,
        Nestable,
        Sequence,
        Sizeable,
        Subscriptable,
    )

__all__ = ["TupleView"]


class TupleView(StdView):
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

    def _normalize_index(self, address: int) -> int:
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
        normalized = self._normalize_index(address)
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

    def __iter__(self) -> Generator[object, None, None]:
        """Iterate over items.

        Yields:
            Items in order
        """
        for i in range(len(self)):
            yield cast_value(self[i])  # type: ignore[misc]

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
            yield cast_value(self[i])  # type: ignore[misc]

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
        self.container.clear_children()

        for index, item in enumerate(value):
            self._set_child_value(index, item)

    def open_child[ViewT: View](self, address: int, view: type[ViewT]) -> ViewT:
        """Open child view at index.

        Args:
            address: Child container index
            view: View class for child

        Returns:
            View instance for child container
        """
        normalized = self._normalize_index(address)
        child_container = Container.create(
            key_.join_segment(self.container.path, normalized),
            self.container.ctx,
            view.get_structure(),
            view.get_protocol(),
        )
        return view(child_container, self.registry)


if TYPE_CHECKING:
    # Verify protocol implementations
    _subscriptable: type[Subscriptable[int, object]] = TupleView
    _convertible: type[Convertible[object]] = TupleView
    _initializable: type[Initializable[Iterable[object]]] = TupleView
    _nestable: type[Nestable[int]] = TupleView
    _containable: type[Containable[object]] = TupleView
    _sizeable: type[Sizeable] = TupleView
    _sequence: type[Sequence[object]] = TupleView
