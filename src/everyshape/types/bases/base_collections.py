"""Collection base classes for Term types.

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


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyshape.term import Term
    from everyshape.types import BoolType, DictType, FloatType, IntType, ListType, StrType


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

    def len_(self) -> IntType:
        """Get length of this value.

        Returns:
            Length value
        """
        from everyshape.ops import LenOp
        from everyshape.types import IntType

        return IntType(LenOp(self))


class IndexableBase[KeyT, ResultValue]:
    """Base for values that support index/key access."""

    def _wrap_indexable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __getitem__(self, key: KeyT) -> ResultValue:
        """Get item at index/key."""
        from everyshape.ops import AtOp

        return cast("ResultValue", self._wrap_indexable_result(AtOp(self, key)))


class SliceableBase[ResultT]:
    """Base for values that support slicing."""

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def slice_(self, start: int | None, stop: int | None, step: int | None = None) -> ResultT:
        """Get slice of this value.

        Args:
            start: Start index
            stop: Stop index
            step: Step size

        Returns:
            Sliced result
        """
        from everyshape.ops import SliceOp

        return cast("ResultT", self._wrap_sliceable_result(SliceOp(self, start, stop, step)))


class ContainableBase[ItemT]:
    """Base for values that support containment testing."""

    def contains(self, item: ItemT) -> BoolType:
        """Check if item is in this value.

        Args:
            item: Item to check

        Returns:
            Boolean result
        """
        from everyshape.ops import ContainsOp
        from everyshape.types import BoolType

        return BoolType(ContainsOp(self, item))


class IterableBase[ElementT, ResultT]:
    """Base for values that support functional iteration operations."""

    def _wrap_iterable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate collection type."""
        raise NotImplementedError()

    def _wrap_element_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate element type."""
        raise NotImplementedError()

    def map_[R](self, func: Callable[[ElementT], R]) -> ResultT:
        """Map function over elements.

        Args:
            func: Function to apply

        Returns:
            Mapped result
        """
        from everyshape.ops import MapOp

        return cast("ResultT", self._wrap_iterable_result(MapOp(self, func)))

    def filter_(self, predicate: Callable[[ElementT], bool]) -> ResultT:
        """Filter elements by predicate.

        Args:
            predicate: Filter function

        Returns:
            Filtered result
        """
        from everyshape.ops import FilterOp

        return cast("ResultT", self._wrap_iterable_result(FilterOp(self, predicate)))

    @overload
    def reduce_(self, func: Callable[[int, ElementT], int], initial: int) -> IntType: ...

    @overload
    def reduce_(self, func: Callable[[float, ElementT], float], initial: float) -> FloatType: ...

    @overload
    def reduce_(self, func: Callable[[str, ElementT], str], initial: str) -> StrType: ...

    @overload
    def reduce_(self, func: Callable[[bool, ElementT], bool], initial: bool) -> BoolType: ...

    @overload
    def reduce_[V](
        self, func: Callable[[list[V], ElementT], list[V]], initial: list[V]
    ) -> ListType[V]: ...

    @overload
    def reduce_[K, V](
        self, func: Callable[[dict[K, V], ElementT], dict[K, V]], initial: dict[K, V]
    ) -> DictType[K, V]: ...

    def reduce_[R](self, func: Callable[[R, ElementT], R], initial: R) -> object:
        """Reduce to single value.

        Args:
            func: Reducer function
            initial: Initial value

        Returns:
            Reduced value
        """
        from everyshape.ops import ReduceOp
        from everyshape.types import AnyType

        return AnyType(ReduceOp(self, func, initial))

    def sum_(self) -> ResultT:
        """Sum all elements.

        Returns:
            Sum
        """
        from everyshape.ops import SumOp

        return cast("ResultT", self._wrap_element_result(SumOp(self)))

    def min_(self) -> ResultT:
        """Get minimum element.

        Returns:
            Minimum
        """
        from everyshape.ops import MinOp

        return cast("ResultT", self._wrap_element_result(MinOp(self)))

    def max_(self) -> ResultT:
        """Get maximum element.

        Returns:
            Maximum
        """
        from everyshape.ops import MaxOp

        return cast("ResultT", self._wrap_element_result(MaxOp(self)))

    def any_(self) -> BoolType:
        """Check if any element is truthy.

        Returns:
            Boolean result
        """
        from everyshape.ops import AnyOp
        from everyshape.types import BoolType

        return BoolType(AnyOp(self))

    def all_(self) -> BoolType:
        """Check if all elements are truthy.

        Returns:
            Boolean result
        """
        from everyshape.ops import AllOp
        from everyshape.types import BoolType

        return BoolType(AllOp(self))


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
        from everyshape.ops import FirstOp

        return cast("ResultT", self._wrap_element_result(FirstOp(self)))

    def last(self) -> ResultT:
        """Get last element.

        Returns:
            Last element
        """
        from everyshape.ops import LastOp

        return cast("ResultT", self._wrap_element_result(LastOp(self)))

    def reversed_(self) -> ResultT:
        """Get reversed sequence.

        Returns:
            Reversed sequence
        """
        from everyshape.ops import ReversedOp

        return cast("ResultT", self._wrap_sliceable_result(ReversedOp(self)))

    def sorted_(self, reverse: bool = False) -> ResultT:
        """Get sorted sequence.

        Args:
            reverse: Sort descending

        Returns:
            Sorted sequence
        """
        from everyshape.ops import SortedOp

        return cast("ResultT", self._wrap_sliceable_result(SortedOp(self, reverse=reverse)))

    def join(self, separator: str) -> StrType:
        """Join string elements.

        Args:
            separator: Separator string

        Returns:
            Joined string
        """
        from everyshape.ops import JoinOp
        from everyshape.types import StrType

        return StrType(JoinOp(self, separator))

    def index(self, value: ElementT) -> IntType:
        """Find index of value.

        Args:
            value: Value to find

        Returns:
            Index
        """
        from everyshape.ops import IndexOfOp
        from everyshape.types import IntType

        return IntType(IndexOfOp(self, value))

    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntType:
        """Find index of first match.

        Args:
            predicate: Match function

        Returns:
            IntType containing index
        """
        from everyshape.ops import FindIndexOp
        from everyshape.types import IntType

        return IntType(FindIndexOp(self, predicate))

    def count(self, value: ElementT) -> IntType:
        """Count occurrences.

        Args:
            value: Value to count

        Returns:
            Count
        """
        from everyshape.ops import CountOp
        from everyshape.types import IntType

        return IntType(CountOp(self, value))


class MappingBase[KeyT, ValueT, ResultT](
    LengthableBase,
    ContainableBase[KeyT],
):
    """Combined base for mapping-like values.

    Provides: len_(), contains(), keys_(), values_(), items_(), get_().

    Subclasses typically also implement __getitem__ for key access.
    """

    def _wrap_keys_result(self, operand: Term) -> Term:
        """Override in subclass to wrap keys sequence result."""
        raise NotImplementedError()

    def _wrap_values_result(self, operand: Term) -> Term:
        """Override in subclass to wrap values sequence result."""
        raise NotImplementedError()

    def _wrap_items_result(self, operand: Term) -> Term:
        """Override in subclass to wrap items sequence result."""
        raise NotImplementedError()

    def _wrap_value_result(self, operand: Term) -> Term:
        """Override in subclass to wrap single value result."""
        raise NotImplementedError()

    def keys_(self) -> ResultT:
        """Get all keys.

        Returns:
            Keys sequence
        """
        from everyshape.types.dict_ops import DictKeysOp

        return cast("ResultT", self._wrap_keys_result(DictKeysOp(self)))

    def values_(self) -> ResultT:
        """Get all values.

        Returns:
            Values sequence
        """
        from everyshape.types.dict_ops import DictValuesOp

        return cast("ResultT", self._wrap_values_result(DictValuesOp(self)))

    def items_(self) -> ResultT:
        """Get all key-value pairs.

        Returns:
            Items sequence
        """
        from everyshape.types.dict_ops import DictItemsOp

        return cast("ResultT", self._wrap_items_result(DictItemsOp(self)))

    def get_(self, key: KeyT, default: ValueT | None = None) -> ResultT:
        """Get value with default.

        Args:
            key: Key to get
            default: Default if not found

        Returns:
            Value or default
        """
        from everyshape.types.dict_ops import DictGetOp

        return cast("ResultT", self._wrap_value_result(DictGetOp(self, key, default)))


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

    def _wrap_set_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set union.

        Args:
            other: Set to union with

        Returns:
            Union set
        """
        from everyshape.types.set_ops import UnionOp

        return cast("ResultT", self._wrap_set_result(UnionOp(self, other)))

    def intersection(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set intersection.

        Args:
            other: Set to intersect with

        Returns:
            Intersection set
        """
        from everyshape.types.set_ops import IntersectionOp

        return cast("ResultT", self._wrap_set_result(IntersectionOp(self, other)))

    def difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set difference.

        Args:
            other: Set to diff with

        Returns:
            Difference set
        """
        from everyshape.types.set_ops import DifferenceOp

        return cast("ResultT", self._wrap_set_result(DifferenceOp(self, other)))

    def symmetric_difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set symmetric difference.

        Args:
            other: Set to symmetric diff with

        Returns:
            Symmetric difference set
        """
        from everyshape.types.set_ops import SymmetricDifferenceOp

        return cast("ResultT", self._wrap_set_result(SymmetricDifferenceOp(self, other)))

    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolType:
        """Check if subset.

        Args:
            other: Set to check against

        Returns:
            Boolean result
        """
        from everyshape.types import BoolType
        from everyshape.types.set_ops import IsSubsetOp

        return BoolType(IsSubsetOp(self, other))

    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolType:
        """Check if superset.

        Args:
            other: Set to check against

        Returns:
            Boolean result
        """
        from everyshape.types import BoolType
        from everyshape.types.set_ops import IsSupersetOp

        return BoolType(IsSupersetOp(self, other))

    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolType:
        """Check if disjoint.

        Args:
            other: Set to check against

        Returns:
            Boolean result
        """
        from everyshape.types import BoolType
        from everyshape.types.set_ops import IsDisjointOp

        return BoolType(IsDisjointOp(self, other))
