"""SetView - Set-like view over container."""

from __future__ import annotations

import hashlib
import pickle
from typing import TYPE_CHECKING, ClassVar

from redwood.tree import ContainerProtocol, ContainerStructure
from redwood.types import cast_value, is_empty

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from collections.abc import Set as PySet

    from redwood.types import (
        Clearable,
        Containable,
        Convertible,
        Initializable,
        MutableSet,
        Sizeable,
    )


__all__ = ["SetView"]


class SetView(StdView):
    """Set-like view over container.

    Provides set interface using values as keys:
    - add(), remove(), discard()
    - __contains__, __len__, __iter__

    Implementation:
    - Uses string representation of values as keys
    - Stores actual values for extraction

    Type Parameters:
        V: Type of values (default: Value)

    Example:
        >>> tags: SetView[str] = SetView(container, registry)
        >>> tags.add("python")
        >>> tags.add("ai")
        >>> print("python" in tags)  # True
        >>> print(len(tags))  # 2
    """

    STRUCTURE: ClassVar[ContainerStructure] = ContainerStructure(4)
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.SET | ContainerProtocol.MUTABLE
    CONTAINER_CLS: ClassVar[type] = set

    def _make_key(self, value: object) -> int:
        """Convert value to storage key.

        Args:
            value: Value to store in set

        Returns:
            Key for storage
        """
        pickled = pickle.dumps(value, protocol=4)  # Use fixed protocol
        # Returns int for use in hash tables, or use .hexdigest() for string
        return int.from_bytes(hashlib.sha256(pickled).digest()[:64], "big")

    def add(self, value: object) -> None:
        """Add value to set.

        Args:
            value: Value to add
        """
        key = self._make_key(value)
        self._set_child_value(key, value)

    def remove(self, value: object) -> None:
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

    def discard(self, value: object) -> None:
        """Remove value from set if present.

        Args:
            value: Value to remove
        """
        key = self._make_key(value)
        self.container.delete_child(key)

    def __contains__(self, obj: object) -> bool:
        """Check if value in set.

        Args:
            obj: Value to check

        Returns:
            True if value in set
        """
        key = self._make_key(obj)
        return self.container.has_child(key)

    def __len__(self) -> int:
        """Get number of values.

        Returns:
            Number of values
        """
        return self.container.count_children()

    def __iter__(self) -> Generator[object, None, None]:
        """Iterate over values.

        Yields:
            Values in set
        """
        for key in self.container.list_child_keys():
            stored_value = self.container.get_child_primitive(key)
            if not is_empty(stored_value):
                yield cast_value(stored_value)  # type: ignore[misc]

    def clear(self) -> None:
        """Remove all values."""
        self.container.clear_children()

    def isdisjoint(self, other: PySet[object]) -> bool:
        """Check if no elements in common with other.

        Args:
            other: Set to compare with

        Returns:
            True if no common elements
        """
        return not any(value in self for value in other)

    def issubset(self, other: PySet[object]) -> bool:
        """Check if all elements are in other.

        Args:
            other: Set to compare with

        Returns:
            True if subset
        """
        return all(value in other for value in self)

    def issuperset(self, other: PySet[object]) -> bool:
        """Check if all elements of other are in this set.

        Args:
            other: Set to compare with

        Returns:
            True if superset
        """
        return all(value in self for value in other)

    # =========================================================================
    # VIEW INTERFACE
    # =========================================================================

    def extract(self) -> set[object]:
        """Extract all values as set.

        Returns:
            Set of all values
        """
        return set(self)

    def store(self, value: Iterable[object]) -> None:
        """Store set contents.

        Args:
            value: Iterable to store
        """
        self.clear()

        for item in value:
            self.add(item)


if TYPE_CHECKING:
    # Verify protocol implementations
    _convertible: type[Convertible[set[object]]] = SetView
    _initializable: type[Initializable[Iterable[object]]] = SetView
    _containable: type[Containable[object]] = SetView
    _sizeable: type[Sizeable] = SetView
    _clearable: type[Clearable] = SetView
    _mutable_set: type[MutableSet[object]] = SetView
