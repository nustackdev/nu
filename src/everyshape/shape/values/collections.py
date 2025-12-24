"""RValue collection type protocols.

This module defines protocols for collection value types composed from
atomic capabilities. These form the collection hierarchy for RValues.

Protocol Hierarchy:
    Container → Collection → Sequence/Mapping/Set
                          → MutableSequence/MutableMapping/MutableSet

Each protocol composes relevant capabilities:
- Sequence: Indexable, Sliceable, Lengthable, Containable
- Mapping: Indexable, Lengthable, Containable (key-based)
- Set: Lengthable, Containable
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .capabilities import (
    Addable,
    Containable,
    Equalable,
    Indexable,
    Lengthable,
    Sliceable,
)


if TYPE_CHECKING:
    from collections.abc import Callable


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
# BASE COLLECTION PROTOCOLS
# =============================================================================


@runtime_checkable
class Container[V, R](
    Containable[V, R],
    Protocol,
):
    """Protocol for container RValues with membership testing.

    Base protocol for all collections. Supports checking if an item exists.

    Type Parameters:
        V: Type of values in the container
        R: Type of results (typically bool or BoolValue)

    Example:
        >>> if isinstance(value, Container):
        ...     exists = value.contains(item)
    """

    pass


@runtime_checkable
class Collection[V, R](
    Container[V, R],
    Lengthable[R],
    Protocol,
):
    """Protocol for sized container RValues.

    Collections have length and support containment testing.

    Type Parameters:
        V: Type of values in the collection
        R: Type of results

    Example:
        >>> if isinstance(value, Collection):
        ...     size = value.len_()
        ...     exists = value.contains(item)
    """

    pass


# =============================================================================
# SEQUENCE PROTOCOLS
# =============================================================================


@runtime_checkable
class Sequence[V, R](
    Collection[V, R],
    Indexable[int, R],
    Sliceable[R],
    Addable[object, R],
    Equalable[object, R],
    Protocol,
):
    """Protocol for read-only sequence RValues.

    Sequences are indexed collections accessed by integer positions.
    Supports indexing, slicing, length, containment, and concatenation.

    Type Parameters:
        V: Type of values in the sequence
        R: Type of results

    Example:
        >>> if isinstance(value, Sequence):
        ...     first = value[0]
        ...     sub = value.slice_(1, 5)
        ...     combined = value + other_seq
    """

    def first(self) -> R:
        """Get the first element.

        Returns:
            First element

        Raises:
            IndexError: If sequence is empty
        """
        ...

    def last(self) -> R:
        """Get the last element.

        Returns:
            Last element

        Raises:
            IndexError: If sequence is empty
        """
        ...

    def reversed_(self) -> R:
        """Get reversed sequence.

        Returns:
            Reversed sequence
        """
        ...

    def sorted_(self, key: Callable[[V], object] | None = None, reverse: bool = False) -> R:
        """Get sorted sequence.

        Args:
            key: Optional key function
            reverse: Sort in descending order

        Returns:
            Sorted sequence
        """
        ...

    def index(self, value: V) -> R:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            Index of first occurrence

        Raises:
            ValueError: If value not found
        """
        ...

    def count(self, value: V) -> R:
        """Count occurrences of value.

        Args:
            value: Value to count

        Returns:
            Number of occurrences
        """
        ...

    def map_[T](self, func: Callable[[V], T]) -> R:
        """Apply function to each element.

        Args:
            func: Function to apply

        Returns:
            Mapped sequence
        """
        ...

    def filter_(self, predicate: Callable[[V], bool]) -> R:
        """Filter elements by predicate.

        Args:
            predicate: Function returning True for elements to keep

        Returns:
            Filtered sequence
        """
        ...

    def reduce_[T](self, func: Callable[[T, V], T], initial: T) -> R:
        """Reduce sequence to single value.

        Args:
            func: Reducer function (accumulator, element) -> new_accumulator
            initial: Initial accumulator value

        Returns:
            Reduced value
        """
        ...

    def sum_(self) -> R:
        """Sum all elements.

        Returns:
            Sum of elements
        """
        ...

    def min_(self) -> R:
        """Get minimum element.

        Returns:
            Minimum element

        Raises:
            ValueError: If sequence is empty
        """
        ...

    def max_(self) -> R:
        """Get maximum element.

        Returns:
            Maximum element

        Raises:
            ValueError: If sequence is empty
        """
        ...

    def any_(self) -> R:
        """Check if any element is truthy.

        Returns:
            True if any element is truthy
        """
        ...

    def all_(self) -> R:
        """Check if all elements are truthy.

        Returns:
            True if all elements are truthy
        """
        ...

    def join(self, separator: str) -> R:
        """Join string elements with separator.

        Args:
            separator: String to join with

        Returns:
            Joined string
        """
        ...


@runtime_checkable
class MutableSequence[V, R](
    Sequence[V, R],
    Protocol,
):
    """Protocol for mutable sequence RValues.

    Extends Sequence with mutation operations.
    In the RValue context, mutations return new RValues rather than
    modifying in place (immutable semantics).

    Type Parameters:
        V: Type of values in the sequence
        R: Type of results

    Example:
        >>> if isinstance(value, MutableSequence):
        ...     extended = value.append_(new_item)
        ...     modified = value.insert_(0, first_item)
    """

    def append_(self, value: V) -> R:
        """Return sequence with value appended.

        Args:
            value: Value to append

        Returns:
            New sequence with appended value
        """
        ...

    def extend_(self, values: Sequence[V, R]) -> R:
        """Return sequence extended with values.

        Args:
            values: Values to extend with

        Returns:
            New extended sequence
        """
        ...

    def insert_(self, index: int, value: V) -> R:
        """Return sequence with value inserted at index.

        Args:
            index: Position to insert at
            value: Value to insert

        Returns:
            New sequence with inserted value
        """
        ...

    def pop_(self, index: int = -1) -> R:
        """Return sequence with element removed.

        Args:
            index: Position to remove from (default: last)

        Returns:
            New sequence without the element
        """
        ...

    def remove_(self, value: V) -> R:
        """Return sequence with first occurrence of value removed.

        Args:
            value: Value to remove

        Returns:
            New sequence without the value

        Raises:
            ValueError: If value not found
        """
        ...

    def clear_(self) -> R:
        """Return empty sequence.

        Returns:
            Empty sequence of same type
        """
        ...


# =============================================================================
# MAPPING PROTOCOLS
# =============================================================================


@runtime_checkable
class Mapping[K, V, R](
    Collection[K, R],
    Indexable[K, R],
    Equalable[object, R],
    Protocol,
):
    """Protocol for read-only mapping RValues.

    Mappings are key-value collections. Supports key-based access,
    length, and containment testing.

    Type Parameters:
        K: Type of keys
        V: Type of values
        R: Type of results

    Example:
        >>> if isinstance(value, Mapping):
        ...     val = value["key"]
        ...     all_keys = value.keys_()
        ...     exists = value.contains("key")
    """

    def keys_(self) -> R:
        """Get all keys.

        Returns:
            Sequence of keys
        """
        ...

    def values_(self) -> R:
        """Get all values.

        Returns:
            Sequence of values
        """
        ...

    def items_(self) -> R:
        """Get all key-value pairs.

        Returns:
            Sequence of (key, value) tuples
        """
        ...

    def get_(self, key: K, default: V | None = None) -> R:
        """Get value with default fallback.

        Args:
            key: Key to retrieve
            default: Default if key not found

        Returns:
            Value or default
        """
        ...

    def map_values[T](self, func: Callable[[V], T]) -> R:
        """Apply function to each value.

        Args:
            func: Function to apply

        Returns:
            Mapping with transformed values
        """
        ...

    def map_items[K2, V2](self, func: Callable[[K, V], tuple[K2, V2]]) -> R:
        """Apply function to each item.

        Args:
            func: Function taking (key, value) returning (new_key, new_value)

        Returns:
            Transformed mapping
        """
        ...

    def filter_(self, predicate: Callable[[K, V], bool]) -> R:
        """Filter items by predicate.

        Args:
            predicate: Function (key, value) -> bool

        Returns:
            Filtered mapping
        """
        ...

    def reduce_[T](self, func: Callable[[T, K, V], T], initial: T) -> R:
        """Reduce mapping to single value.

        Args:
            func: Reducer function (accumulator, key, value) -> new_accumulator
            initial: Initial accumulator value

        Returns:
            Reduced value
        """
        ...


@runtime_checkable
class MutableMapping[K, V, R](
    Mapping[K, V, R],
    Protocol,
):
    """Protocol for mutable mapping RValues.

    Extends Mapping with mutation operations.
    In the RValue context, mutations return new RValues.

    Type Parameters:
        K: Type of keys
        V: Type of values
        R: Type of results

    Example:
        >>> if isinstance(value, MutableMapping):
        ...     updated = value.set_("key", new_value)
        ...     without_key = value.delete_("old_key")
    """

    def set_(self, key: K, value: V) -> R:
        """Return mapping with key set to value.

        Args:
            key: Key to set
            value: Value to set

        Returns:
            New mapping with updated key
        """
        ...

    def delete_(self, key: K) -> R:
        """Return mapping with key removed.

        Args:
            key: Key to remove

        Returns:
            New mapping without key

        Raises:
            KeyError: If key not found
        """
        ...

    def update_(self, other: Mapping[K, V, R]) -> R:
        """Return mapping updated with other.

        Args:
            other: Mapping to merge in

        Returns:
            Merged mapping
        """
        ...

    def pop_(self, key: K, default: V | None = None) -> R:
        """Return mapping with key removed and the removed value.

        Args:
            key: Key to remove
            default: Default if key not found

        Returns:
            Tuple of (new_mapping, removed_value)
        """
        ...

    def clear_(self) -> R:
        """Return empty mapping.

        Returns:
            Empty mapping of same type
        """
        ...


# =============================================================================
# SET PROTOCOLS
# =============================================================================


@runtime_checkable
class Set[V, R](
    Collection[V, R],
    Equalable[object, R],
    Protocol,
):
    """Protocol for read-only set RValues.

    Sets are unordered collections of unique values.
    Supports containment testing, length, and set operations.

    Type Parameters:
        V: Type of values in the set
        R: Type of results

    Example:
        >>> if isinstance(value, Set):
        ...     exists = value.contains(item)
        ...     combined = value.union_(other_set)
    """

    def union_(self, other: Set[V, R]) -> R:
        """Return union with other set.

        Args:
            other: Set to union with

        Returns:
            Union set
        """
        ...

    def intersection_(self, other: Set[V, R]) -> R:
        """Return intersection with other set.

        Args:
            other: Set to intersect with

        Returns:
            Intersection set
        """
        ...

    def difference_(self, other: Set[V, R]) -> R:
        """Return difference with other set.

        Args:
            other: Set to subtract

        Returns:
            Difference set
        """
        ...

    def symmetric_difference_(self, other: Set[V, R]) -> R:
        """Return symmetric difference with other set.

        Args:
            other: Set to compute symmetric difference with

        Returns:
            Symmetric difference set
        """
        ...

    def issubset_(self, other: Set[V, R]) -> R:
        """Check if this is a subset of other.

        Args:
            other: Set to compare with

        Returns:
            True if subset
        """
        ...

    def issuperset_(self, other: Set[V, R]) -> R:
        """Check if this is a superset of other.

        Args:
            other: Set to compare with

        Returns:
            True if superset
        """
        ...

    def isdisjoint_(self, other: Set[V, R]) -> R:
        """Check if this has no elements in common with other.

        Args:
            other: Set to compare with

        Returns:
            True if disjoint
        """
        ...


@runtime_checkable
class MutableSet[V, R](
    Set[V, R],
    Protocol,
):
    """Protocol for mutable set RValues.

    Extends Set with mutation operations.
    In the RValue context, mutations return new RValues.

    Type Parameters:
        V: Type of values in the set
        R: Type of results

    Example:
        >>> if isinstance(value, MutableSet):
        ...     with_item = value.add_(new_item)
        ...     without_item = value.discard_(old_item)
    """

    def add_(self, value: V) -> R:
        """Return set with value added.

        Args:
            value: Value to add

        Returns:
            New set with added value
        """
        ...

    def remove_(self, value: V) -> R:
        """Return set with value removed.

        Args:
            value: Value to remove

        Returns:
            New set without value

        Raises:
            KeyError: If value not found
        """
        ...

    def discard_(self, value: V) -> R:
        """Return set with value removed if present.

        Args:
            value: Value to discard

        Returns:
            New set without value (no error if absent)
        """
        ...

    def clear_(self) -> R:
        """Return empty set.

        Returns:
            Empty set of same type
        """
        ...

    def update_(self, other: Set[V, R]) -> R:
        """Return set updated with other.

        Args:
            other: Set to add values from

        Returns:
            Updated set
        """
        ...
