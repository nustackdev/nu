"""Collection protocol hierarchy.

This module defines collection protocols composed from atomic capabilities.
Follows Python's collections.abc hierarchy while using EveryShape's capability system.

Protocol Hierarchy:
    Container → Collection → Sequence/Mapping/Set
                          → MutableSequence/MutableMapping/MutableSet
"""

from __future__ import annotations

from collections.abc import Iterator as PyIterator
from collections.abc import Mapping as PyMapping
from collections.abc import Set as PySet
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .capabilities import (
    Appendable,
    Assignable,
    ChildWatchable,
    Clearable,
    Containable,
    Convertible,
    Deletable,
    Initializable,
    Sizeable,
    Subscriptable,
    Watchable,
)


if TYPE_CHECKING:
    from everyshape.types import Empty


__all__ = [
    "Collection",
    "Container",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Sequence",
    "Set",
]


# =============================================================================
# BASE COLLECTIONS
# =============================================================================


@runtime_checkable
class Container[V](
    Containable[V],
    Protocol,
):
    """Protocol for containers with membership testing.

    Base protocol for all collections. Supports checking if an item exists.

    Type Parameters:
        V: The type of values stored in the container

    Example:
        >>> if isinstance(view, Container):
        ...     if value in view:
        ...         print("Value exists")
    """

    pass


@runtime_checkable
class Collection[V](
    Container[V],
    Sizeable,
    Protocol,
):
    """Protocol for sized iterable containers.

    Foundation protocol for all sized collections. Supports membership testing,
    size queries, and iteration.

    Type Parameters:
        V: The type of values yielded by iteration

    Example:
        >>> if isinstance(view, Collection):
        ...     size = len(view)
        ...     for item in view:
        ...         print(item)
    """

    # def __iter__(self) -> PyIterator[V]:
    #     """Iterate over items.

    #     Returns:
    #         Iterator over items in the collection
    #     """
    #     ...


# =============================================================================
# SEQUENCES
# =============================================================================


@runtime_checkable
class Sequence[V](
    Collection[int],
    Subscriptable[int, V],
    Convertible[PyIterator[V]],
    Protocol,
):
    """Protocol for read-only sequences.

    Sequences are indexed collections accessed by integer positions.
    Supports iteration, size queries, membership testing, and subscript access.

    Type Parameters:
        V: The type of values stored in the sequence

    Example:
        >>> if isinstance(view, Sequence):
        ...     first = view[0]
        ...     if value in view:
        ...         index = view.index(value)
    """

    # def __reversed__(self) -> PyIterator[V]:
    #     """Iterate in reverse order.

    #     Returns:
    #         Iterator over items in reverse order
    #     """
    #     ...

    # def index(self, value: V) -> int:
    #     """Find index of first occurrence of value.

    #     Args:
    #         value: Value to find

    #     Returns:
    #         Index of first occurrence

    #     Raises:
    #         ValueError: If value not found
    #     """
    #     ...

    # def count(self, value: V) -> int:
    #     """Count occurrences of value.

    #     Args:
    #         value: Value to count

    #     Returns:
    #         Number of occurrences
    #     """
    #     ...


@runtime_checkable
class MutableSequence[V](
    Sequence[V],
    Assignable[int, V],
    Deletable[int],
    Appendable[V],
    Clearable,
    Initializable[PyIterator[V]],
    Watchable,
    ChildWatchable[int],
    Protocol,
):
    """Protocol for mutable sequences.

    Extends Sequence with mutation operations: assignment, deletion,
    insertion, and appending.

    Type Parameters:
        V: The type of values stored in the sequence

    Example:
        >>> if isinstance(view, MutableSequence):
        ...     view[0] = value
        ...     view.append(value)
        ...     view.insert(1, value)
        ...     del view[0]
    """

    def insert(self, address: int, value: V) -> None:
        """Insert value at index.

        Args:
            address: Position to insert at
            value: Value to insert
        """
        ...

    # def reverse(self) -> None:
    #     """Reverse the sequence in-place."""
    #     ...

    # def extend(self, values: PyIterator[V]) -> None:
    #     """Extend sequence with values from iterable.

    #     Args:
    #         values: Values to append
    #     """
    #     ...

    def pop(self, address: int = -1) -> V | Empty:
        """Remove and return item at index.

        Args:
            address: Position to remove from (default: last item)

        Returns:
            Removed value

        Raises:
            IndexError: If index out of range
        """
        ...

    # def remove(self, value: V) -> None:
    #     """Remove first occurrence of value.

    #     Args:
    #         value: Value to remove

    #     Raises:
    #         ValueError: If value not found
    #     """
    #     ...


# =============================================================================
# MAPPINGS
# =============================================================================


@runtime_checkable
class Mapping[K, V](
    Collection[K],
    Subscriptable[K, V],
    Convertible[PyMapping[K, V]],
    Protocol,
):
    """Protocol for read-only mappings.

    Mappings are key-value collections accessed by keys.
    Supports iteration over keys, size queries, membership testing,
    and subscript access.

    Type Parameters:
        K: The type of keys
        V: The type of values

    Example:
        >>> if isinstance(view, Mapping):
        ...     value = view["key"]
        ...     if "key" in view:
        ...         keys = list(view.keys())
    """

    def keys(self) -> PyIterator[K]:
        """Get all keys.

        Returns:
            List of all keys
        """
        ...

    def values(self) -> PyIterator[V]:
        """Get all values.

        Returns:
            List of all values
        """
        ...

    def items(self) -> PyIterator[tuple[K, V]]:
        """Get all key-value pairs.

        Returns:
            List of (key, value) tuples
        """
        ...

    # def get(self, address: K, default: V | Empty = EMPTY) -> V | Empty:
    #     """Get value with default fallback.

    #     Args:
    #         address: Key to retrieve
    #         default: Default if key not found

    #     Returns:
    #         Value or default
    #     """
    #     ...


@runtime_checkable
class MutableMapping[K, V](
    Mapping[K, V],
    Assignable[K, V],
    Deletable[K],
    Clearable,
    Initializable[PyMapping[K, V]],
    Watchable,
    ChildWatchable[K],
    Protocol,
):
    """Protocol for mutable mappings.

    Extends Mapping with mutation operations: assignment, deletion,
    and updates.

    Type Parameters:
        K: The type of keys
        V: The type of values

    Example:
        >>> if isinstance(view, MutableMapping):
        ...     view["key"] = value
        ...     del view["key"]
        ...     view.update({"key": value})
        ...     view.clear()
    """

    # def pop(self, address: K, default: V | Empty = EMPTY) -> V | Empty:
    #     """Remove and return value for key.

    #     Args:
    #         address: Key to remove
    #         default: Default if key not found

    #     Returns:
    #         Removed value or default

    #     Raises:
    #         KeyError: If key not found and no default
    #     """
    #     ...

    # def popitem(self) -> tuple[K, V]:
    #     """Remove and return arbitrary key-value pair.

    #     Returns:
    #         (key, value) tuple

    #     Raises:
    #         KeyError: If mapping is empty
    #     """
    #     ...

    def update(self, other: PyMapping[K, V]) -> None:
        """Update mapping with key-value pairs from other.

        Args:
            other: Mapping to update from
        """
        ...

    # def setdefault(self, address: K, default: V) -> V:
    #     """Get value for key, setting default if not present.

    #     Args:
    #         address: Key to get/set
    #         default: Value to set if key not present

    #     Returns:
    #         Existing or newly set value
    #     """
    #     ...


# =============================================================================
# SETS
# =============================================================================


@runtime_checkable
class Set[V](
    Collection[V],
    Convertible[PySet[V]],
    Protocol,
):
    """Protocol for read-only sets.

    Sets are unordered collections of unique values.
    Supports membership testing, size queries, iteration, and set operations.

    Type Parameters:
        V: The type of values in the set

    Example:
        >>> if isinstance(view, Set):
        ...     if value in view:
        ...         if view.issubset(other):
        ...             print("Is subset")
    """

    def isdisjoint(self, other: PySet[V]) -> bool:
        """Check if no elements in common with other.

        Args:
            other: Set to compare with

        Returns:
            True if no common elements
        """
        ...

    def issubset(self, other: PySet[V]) -> bool:
        """Check if all elements are in other.

        Args:
            other: Set to compare with

        Returns:
            True if subset
        """
        ...

    def issuperset(self, other: PySet[V]) -> bool:
        """Check if all elements of other are in this set.

        Args:
            other: Set to compare with

        Returns:
            True if superset
        """
        ...


@runtime_checkable
class MutableSet[V](
    Set[V],
    Clearable,
    Initializable[PySet[V]],
    Watchable,
    Protocol,
):
    """Protocol for mutable sets.

    Extends Set with mutation operations: adding, removing, and clearing.
    Unlike sequences and mappings, sets do not support indexed access or
    appending - they use add() and discard() for value-based operations.

    Type Parameters:
        V: The type of values in the set

    Example:
        >>> if isinstance(view, MutableSet):
        ...     view.add(value)
        ...     view.discard(value)
        ...     view.clear()
    """

    def add(self, value: V) -> None:
        """Add value to set.

        Args:
            value: Value to add
        """
        ...

    def remove(self, value: V) -> None:
        """Remove value from set.

        Args:
            value: Value to remove

        Raises:
            KeyError: If value not in set
        """
        ...

    # def discard(self, value: V) -> None:
    #     """Remove value from set if present.

    #     Args:
    #         value: Value to remove (no error if absent)
    #     """
    #     ...
