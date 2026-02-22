"""SetView - Set-like view over container."""

from __future__ import annotations

import hashlib
import pickle  # nosec: F401
from collections.abc import MutableSet
from typing import TYPE_CHECKING, ClassVar

from pv.container import ContainerProtocol, ContainerStructure
from pv.types import is_empty
from pv.view import (
    ChildNestedSetBase,
    ChildObservableBase,
    ChildPrimitiveSetBase,
    MetadataBasedChildrenCountBase,
    ObservableBase,
    UnsafePrimitiveOpsBase,
)

from .base import StdView


if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from collections.abc import Set as PySet

    from pv.collections import MutableSetView
    from pv.traits import (
        ChildObservable,
        Clearable,
        Containable,
        Convertible,
        Initializable,
        Observable,
        Sizeable,
    )


__all__ = ["SetView"]


class SetView(
    ObservableBase,
    ChildObservableBase[object],
    MetadataBasedChildrenCountBase,
    ChildNestedSetBase,
    ChildPrimitiveSetBase,
    UnsafePrimitiveOpsBase,
    StdView,
):
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

    def _make_key(self, value: object) -> str:
        """Convert value to storage key.

        Args:
            value: Value to store in set

        Returns:
            Key for storage
        """
        pickled = pickle.dumps(value, protocol=4)  # Use fixed protocol
        # Returns int for use in hash tables, or use .hexdigest() for string
        return hashlib.sha256(pickled).hexdigest()[:64]

    @classmethod
    def is_address_static(cls, address: object) -> bool:
        """Set addresses are hashed — never passthrough."""
        return False

    def normalize_address(self, address: object) -> str:
        """Normalize value address to an internal storage key."""
        return self._make_key(address)

    def add(self, value: object) -> None:
        """Add value to set.

        Args:
            value: Value to add
        """
        key = self._make_key(value)
        is_new = not self.container.exists_child(key)
        self._set_child_value(key, value)
        # Update length metadata if new value
        if is_new:
            self._increment_length()

    def remove(self, value: object) -> None:
        """Remove value from set.

        Args:
            value: Value to remove

        Raises:
            KeyError: If value not in set
        """
        self.ensure_created()
        key = self._make_key(value)
        if not self.container.exists_child(key):
            raise KeyError(value)
        self.container.delete_child(key)
        self._decrement_length()

    def discard(self, value: object) -> None:
        """Remove value from set if present.

        Args:
            value: Value to remove
        """
        self.ensure_created()
        key = self._make_key(value)
        if self.container.exists_child(key):
            self.container.delete_child(key)
            self._decrement_length()

    def __contains__(self, obj: object) -> bool:
        """Check if value in set.

        Args:
            obj: Value to check

        Returns:
            True if value in set
        """
        key = self._make_key(obj)
        return self.container.exists_child(key)

    def __iter__(self) -> Generator[object, None, None]:
        """Iterate over values.

        Yields:
            Values in set
        """
        for key in self.container.iter_child_keys():
            stored_value = self.container.get_child_primitive(key)
            if not is_empty(stored_value):
                yield stored_value

    def clear(self) -> None:
        """Remove all values."""
        self.ensure_created()
        self.container.clear_children()
        # Reset length metadata
        self._set_length(0)

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

    def __or__(self, other: object) -> set[object]:
        """Set union: self | other."""
        return set(self) | set(other)

    def __and__(self, other: object) -> set[object]:
        """Set intersection: self & other."""
        return set(self) & set(other)

    def __sub__(self, other: object) -> set[object]:
        """Set difference: self - other."""
        return set(self) - set(other)

    def __xor__(self, other: object) -> set[object]:
        """Set symmetric difference: self ^ other."""
        return set(self) ^ set(other)

    def __le__(self, other: object) -> bool:
        """Test if subset: self <= other."""
        return self.issubset(other)

    def __ge__(self, other: object) -> bool:
        """Test if superset: self >= other."""
        return self.issuperset(other)

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

        # Batch store and update length once at end
        count = 0
        for item in value:
            key = self._make_key(item)
            if not self.container.exists_child(key):
                self._set_child_value(key, item)
                count += 1

        # Set final length metadata
        self._set_length(count)


MutableSet.register(SetView)


if TYPE_CHECKING:
    # Verify protocol implementations
    _convertible: type[Convertible[set[object]]] = SetView
    _initializable: type[Initializable[Iterable[object]]] = SetView
    _containable: type[Containable[object]] = SetView
    _sizeable: type[Sizeable] = SetView
    _clearable: type[Clearable] = SetView
    _mutable_set: type[MutableSetView[object]] = SetView
    _Observable: type[Observable] = SetView
    _Observable_children: type[ChildObservable] = SetView
