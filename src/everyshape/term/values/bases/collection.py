"""Collection base classes for RValue types.

This module provides collection operation mixins including:
- LengthableBase - len_()
- IndexableBase - __getitem__ for int keys
- SliceableBase - __getitem__ for slices, slice_()
- ContainableBase - contains()
- IterableBase - map_(), filter_(), reduce_(), etc.
- SequenceBase - Combines collection ops for sequences
- MappingBase - Combines collection ops for mappings
- SetBase - Combines collection ops for sets
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

from ..conversion import literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from ...term import RValue
    from ..values import (
        BoolValue,
        DictValue,
        FloatValue,
        IntValue,
        ListValue,
        StrValue,
    )


__all__ = [
    "ContainableBase",
    "IndexableBase",
    "IterableBase",
    "LengthableBase",
    "MappingBase",
    "SequenceBase",
    "SetBase",
    "SliceableBase",
]


class LengthableBase:
    """Base for values that have a length."""

    def len_(self) -> IntValue:
        """Get length of this value.

        Returns:
            Length value
        """
        from ...comps.types.sequence import LenOp
        from ..values import IntValue

        return IntValue(LenOp(self))


class IndexableBase[KeyT, ResultValue]:
    """Base for values that support index/key access."""

    def _wrap_indexable_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def __getitem__(self, key: KeyT) -> ResultValue:
        """Get item at index/key."""
        from ...comps.types.sequence import AtOp

        return cast("ResultValue", self._wrap_indexable_result(AtOp(self, literal(key))))


class SliceableBase[ResultT]:
    """Base for values that support slicing."""

    def _wrap_sliceable_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate type."""
        return operand

    def slice_(self, start: int | None, stop: int | None, step: int | None = None) -> ResultT:
        """Get slice of this value.

        Args:
            start: Start index
            stop: Stop index
            step: Step size

        Returns:
            Sliced result
        """
        from ...comps.types.sequence import SliceOp

        return cast("ResultT", self._wrap_sliceable_result(SliceOp(self, start, stop, step)))


class ContainableBase[ItemT]:
    """Base for values that support containment testing."""

    def contains(self, item: ItemT) -> BoolValue:
        """Check if item is in this value.

        Args:
            item: Item to check

        Returns:
            Boolean result
        """
        from ...comps.types.mapping import ContainsOp
        from ..values import BoolValue

        return BoolValue(ContainsOp(self, literal(item)))


class IterableBase[ElementT, ResultT]:
    """Base for values that support functional iteration operations."""

    def _wrap_iterable_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate collection type."""
        return operand

    def _wrap_element_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate element type."""
        return operand

    def map_[R](self, func: Callable[[ElementT], R]) -> ResultT:
        """Map function over elements.

        Args:
            func: Function to apply

        Returns:
            Mapped result
        """
        from ...comps.types.sequence import MapOp

        return cast("ResultT", self._wrap_iterable_result(MapOp(self, func)))

    def filter_(self, predicate: Callable[[ElementT], bool]) -> ResultT:
        """Filter elements by predicate.

        Args:
            predicate: Filter function

        Returns:
            Filtered result
        """
        from ...comps.types.sequence import FilterOp

        return cast("ResultT", self._wrap_iterable_result(FilterOp(self, predicate)))

    @overload
    def reduce_(self, func: Callable[[int, ElementT], int], initial: int) -> IntValue: ...

    @overload
    def reduce_(self, func: Callable[[float, ElementT], float], initial: float) -> FloatValue: ...

    @overload
    def reduce_(self, func: Callable[[str, ElementT], str], initial: str) -> StrValue: ...

    @overload
    def reduce_(self, func: Callable[[bool, ElementT], bool], initial: bool) -> BoolValue: ...

    @overload
    def reduce_[V](
        self, func: Callable[[list[V], ElementT], list[V]], initial: list[V]
    ) -> ListValue[V]: ...

    @overload
    def reduce_[K, V](
        self, func: Callable[[dict[K, V], ElementT], dict[K, V]], initial: dict[K, V]
    ) -> DictValue[K, V]: ...

    def reduce_[R](self, func: Callable[[R, ElementT], R], initial: R) -> object:
        """Reduce to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Reduced value
        """
        from ...comps.types.sequence import ReduceOp
        from ..values import UnknownValue

        return UnknownValue(ReduceOp(self, func, initial))

    def sum_(self) -> ResultT:
        """Sum all elements.

        Returns:
            Sum
        """
        from ...comps.types.sequence import SumOp

        return cast("ResultT", self._wrap_element_result(SumOp(self)))

    def min_(self) -> ResultT:
        """Get minimum element.

        Returns:
            Minimum
        """
        from ...comps.types.sequence import MinOp

        return cast("ResultT", self._wrap_element_result(MinOp(self)))

    def max_(self) -> ResultT:
        """Get maximum element.

        Returns:
            Maximum
        """
        from ...comps.types.sequence import MaxOp

        return cast("ResultT", self._wrap_element_result(MaxOp(self)))

    def any_(self) -> BoolValue:
        """Check if any element is truthy.

        Returns:
            Boolean result
        """
        from ...comps.types.sequence import AnyOp
        from ..values import BoolValue

        return BoolValue(AnyOp(self))

    def all_(self) -> BoolValue:
        """Check if all elements are truthy.

        Returns:
            Boolean result
        """
        from ...comps.types.sequence import AllOp
        from ..values import BoolValue

        return BoolValue(AllOp(self))


class SequenceBase[ElementT, ResultT](
    LengthableBase,
    SliceableBase[ResultT],
    ContainableBase[ElementT],
    IterableBase[ElementT, ResultT],
):
    """Combined base for sequence-like values.

    Provides: len_(), slice_(), contains(), map_(), filter_(), reduce_(),
    sum_(), min_(), max_(), any_(), all_().

    Subclasses typically also implement __getitem__ for indexing.
    """

    def first(self) -> ResultT:
        """Get first element.

        Returns:
            First element
        """
        from ...comps.types.sequence import FirstOp

        return cast("ResultT", self._wrap_element_result(FirstOp(self)))

    def last(self) -> ResultT:
        """Get last element.

        Returns:
            Last element
        """
        from ...comps.types.sequence import LastOp

        return cast("ResultT", self._wrap_element_result(LastOp(self)))

    def reversed_(self) -> ResultT:
        """Get reversed sequence.

        Returns:
            Reversed sequence
        """
        from ...comps.types.sequence import ReversedOp

        return cast("ResultT", self._wrap_sliceable_result(ReversedOp(self)))

    def sorted_(self, reverse: bool = False) -> ResultT:
        """Get sorted sequence.

        Args:
            reverse: Sort descending

        Returns:
            Sorted sequence
        """
        from ...comps.types.sequence import SortedOp

        return cast("ResultT", self._wrap_sliceable_result(SortedOp(self, reverse=reverse)))

    def join(self, separator: str) -> StrValue:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            Joined string
        """
        from ...comps.types.sequence import JoinOp
        from ..values import StrValue

        return StrValue(JoinOp(self, literal(separator)))

    def index(self, value: ElementT) -> IntValue:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            Index
        """
        from ...comps.types.sequence import IndexOfOp
        from ..values import IntValue

        return IntValue(IndexOfOp(self, literal(value)))

    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntValue:
        """Find index of first match.

        Args:
            predicate: Match function

        Returns:
            IntValue containing index
        """
        from ...comps.types.sequence import FindIndexOp
        from ..values import IntValue

        return IntValue(FindIndexOp(self, predicate))

    def count(self, value: ElementT) -> IntValue:
        """Count occurrences.

        Args:
            value: Value to count

        Returns:
            Count
        """
        from ...comps.types.sequence import CountOp
        from ..values import IntValue

        return IntValue(CountOp(self, literal(value)))


class MappingBase[KeyT, ValueT, ResultT](
    LengthableBase,
    ContainableBase[KeyT],
):
    """Combined base for mapping-like values.

    Provides: len_(), contains(), keys_(), values_(), items_(), get_().

    Subclasses typically also implement __getitem__ for key access.
    """

    def _wrap_keys_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap keys sequence result."""
        return operand

    def _wrap_values_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap values sequence result."""
        return operand

    def _wrap_items_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap items sequence result."""
        return operand

    def _wrap_value_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap single value result."""
        return operand

    def keys_(self) -> ResultT:
        """Get all keys.

        Returns:
            Keys sequence
        """
        from ...comps.types.mapping import DictKeysOp

        return cast("ResultT", self._wrap_keys_result(DictKeysOp(self)))

    def values_(self) -> ResultT:
        """Get all values.

        Returns:
            Values sequence
        """
        from ...comps.types.mapping import DictValuesOp

        return cast("ResultT", self._wrap_values_result(DictValuesOp(self)))

    def items_(self) -> ResultT:
        """Get all key-value pairs.

        Returns:
            Items sequence
        """
        from ...comps.types.mapping import DictItemsOp

        return cast("ResultT", self._wrap_items_result(DictItemsOp(self)))

    def get_(self, key: KeyT, default: ValueT | None = None) -> ResultT:
        """Get value with default.

        Args:
            key: Key to get
            default: Default if not found

        Returns:
            Value or default
        """
        from ...comps.types.mapping import DictGetOp

        return cast(
            "ResultT", self._wrap_value_result(DictGetOp(self, literal(key), literal(default)))
        )


# =============================================================================
# SET BASES
# =============================================================================


class SetBase[ElementT, ResultT](
    LengthableBase,
    ContainableBase[ElementT],
):
    """Combined base for set-like values.

    Provides: len_(), contains(), union(), intersection(), difference(),
    symmetric_difference(), issubset(), issuperset(), isdisjoint().
    """

    def _wrap_set_result(self, operand: RValue) -> RValue:
        """Override in subclass to wrap result in appropriate set type."""
        return operand

    def union(self, other: set[ElementT] | frozenset[ElementT] | RValue) -> ResultT:
        """Set union.

        Args:
            other: Set to union with

        Returns:
            Union set
        """
        from ...comps.types.set import UnionOp

        return cast("ResultT", self._wrap_set_result(UnionOp(self, literal(other))))

    def intersection(self, other: set[ElementT] | frozenset[ElementT] | RValue) -> ResultT:
        """Set intersection.

        Args:
            other: Set to intersect with

        Returns:
            Intersection set
        """
        from ...comps.types.set import IntersectionOp

        return cast("ResultT", self._wrap_set_result(IntersectionOp(self, literal(other))))

    def difference(self, other: set[ElementT] | frozenset[ElementT] | RValue) -> ResultT:
        """Set difference.

        Args:
            other: Set to diff with

        Returns:
            Difference set
        """
        from ...comps.types.set import DifferenceOp

        return cast("ResultT", self._wrap_set_result(DifferenceOp(self, literal(other))))

    def symmetric_difference(self, other: set[ElementT] | frozenset[ElementT] | RValue) -> ResultT:
        """Set symmetric difference.

        Args:
            other: Set to symmetric diff with

        Returns:
            Symmetric difference set
        """
        from ...comps.types.set import SymmetricDifferenceOp

        return cast("ResultT", self._wrap_set_result(SymmetricDifferenceOp(self, literal(other))))

    def issubset(self, other: set[ElementT] | frozenset[ElementT] | RValue) -> BoolValue:
        """Check if subset.

        Args:
            other: Set to check against

        Returns:
            Boolean result
        """
        from ...comps.types.set import IsSubsetOp
        from ..values import BoolValue

        return BoolValue(IsSubsetOp(self, literal(other)))

    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | RValue) -> BoolValue:
        """Check if superset.

        Args:
            other: Set to check against

        Returns:
            Boolean result
        """
        from ...comps.types.set import IsSupersetOp
        from ..values import BoolValue

        return BoolValue(IsSupersetOp(self, literal(other)))

    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | RValue) -> BoolValue:
        """Check if disjoint.

        Args:
            other: Set to check against

        Returns:
            Boolean result
        """
        from ...comps.types.set import IsDisjointOp
        from ..values import BoolValue

        return BoolValue(IsDisjointOp(self, literal(other)))
