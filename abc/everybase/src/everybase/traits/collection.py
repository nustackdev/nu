"""Collection capability traits for refs.

Atomic traits:
- Lengthable: len_()
- Indexable: __getitem__
- Sliceable: slice_()
- Containable: contains()
- Iterable: map_(), filter_(), reduce_(), sum_(), min_(), max_(), any_(), all_()

Combined traits:
- Sequence = Lengthable + Sliceable + Containable + Iterable + first/last/reversed/sorted/join/index/count
- Mapping = Lengthable + Containable + keys/values/items/get
- SetLike = Lengthable + Containable + set operations
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyabc import BoolArg, IntArg, StrArg, Term
    from everybase.py import BoolRef, DictRef, FloatRef, IntRef, ListRef, StrRef


__all__ = [
    "Containable",
    "Indexable",
    "Iterable",
    "Lengthable",
    "Mapping",
    "Sequence",
    "SetLike",
    "Sliceable",
]


class Lengthable:
    """Trait for values that have a length."""

    def len_(self) -> IntRef:
        """Get length of this value."""
        from everybase.morphisms import LenOp
        from everybase.py import IntRef

        return IntRef(LenOp(self))


class Indexable[KeyT, ResultValue]:
    """Trait for values that support index/key access."""

    def _wrap_indexable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __getitem__(self, key: KeyT) -> ResultValue:
        """Get item at index/key."""
        from everybase.morphisms import AtOp

        return cast("ResultValue", self._wrap_indexable_result(AtOp(self, key)))


class Sliceable[ResultT]:
    """Trait for values that support slicing."""

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def slice_(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT:
        """Get slice of this value."""
        from everybase.morphisms import SliceOp

        return cast("ResultT", self._wrap_sliceable_result(SliceOp(self, start, stop, step)))


class Containable[ItemT]:
    """Trait for values that support containment testing."""

    def contains(self, item: ItemT) -> BoolRef:
        """Check if item is in this value."""
        from everybase.morphisms import ContainsOp
        from everybase.py import BoolRef

        return BoolRef(ContainsOp(self, item))


class Iterable[ElementT, ResultT]:
    """Trait for values that support functional iteration operations."""

    def _wrap_iterable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate collection type."""
        raise NotImplementedError()

    def _wrap_element_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate element type."""
        raise NotImplementedError()

    def map_[R](self, func: Callable[[ElementT], R]) -> ResultT:
        """Map function over elements."""
        from everybase.morphisms import MapOp

        return cast("ResultT", self._wrap_iterable_result(MapOp(self, func)))

    def filter_(self, predicate: Callable[[ElementT], bool]) -> ResultT:
        """Filter elements by predicate."""
        from everybase.morphisms import FilterOp

        return cast("ResultT", self._wrap_iterable_result(FilterOp(self, predicate)))

    @overload
    def reduce_(self, func: Callable[[int, ElementT], int], initial: int) -> IntRef: ...

    @overload
    def reduce_(self, func: Callable[[float, ElementT], float], initial: float) -> FloatRef: ...

    @overload
    def reduce_(self, func: Callable[[str, ElementT], str], initial: str) -> StrRef: ...

    @overload
    def reduce_(self, func: Callable[[bool, ElementT], bool], initial: bool) -> BoolRef: ...

    @overload
    def reduce_[V](
        self, func: Callable[[list[V], ElementT], list[V]], initial: list[V]
    ) -> ListRef[V]: ...

    @overload
    def reduce_[K, V](
        self, func: Callable[[dict[K, V], ElementT], dict[K, V]], initial: dict[K, V]
    ) -> DictRef[K, V]: ...

    def reduce_[R](self, func: Callable[[R, ElementT], R], initial: R) -> object:
        """Reduce to single value."""
        from everybase.morphisms import ReduceOp
        from everybase.py import AnyRef

        return AnyRef(ReduceOp(self, func, initial))

    def sum_(self) -> ResultT:
        """Sum all elements."""
        from everybase.morphisms import SumOp

        return cast("ResultT", self._wrap_element_result(SumOp(self)))

    def min_(self) -> ResultT:
        """Get minimum element."""
        from everybase.morphisms import MinOp

        return cast("ResultT", self._wrap_element_result(MinOp(self)))

    def max_(self) -> ResultT:
        """Get maximum element."""
        from everybase.morphisms import MaxOp

        return cast("ResultT", self._wrap_element_result(MaxOp(self)))

    def any_(self) -> BoolRef:
        """Check if any element is truthy."""
        from everybase.morphisms import AnyOp
        from everybase.py import BoolRef

        return BoolRef(AnyOp(self))

    def all_(self) -> BoolRef:
        """Check if all elements are truthy."""
        from everybase.morphisms import AllOp
        from everybase.py import BoolRef

        return BoolRef(AllOp(self))


class Sequence[ElementT, ResultT](
    Lengthable,
    Sliceable[ResultT],
    Containable[ElementT],
    Iterable[ElementT, ResultT],
):
    """Combined trait for sequence-like values."""

    def first(self) -> ResultT:
        """Get first element."""
        from everybase.morphisms import FirstOp

        return cast("ResultT", self._wrap_element_result(FirstOp(self)))

    def last(self) -> ResultT:
        """Get last element."""
        from everybase.morphisms import LastOp

        return cast("ResultT", self._wrap_element_result(LastOp(self)))

    def reversed_(self) -> ResultT:
        """Get reversed sequence."""
        from everybase.morphisms import ReversedOp

        return cast("ResultT", self._wrap_sliceable_result(ReversedOp(self)))

    def sorted_(self, reverse: BoolArg = False) -> ResultT:
        """Get sorted sequence."""
        from everybase.morphisms import SortedOp

        return cast("ResultT", self._wrap_sliceable_result(SortedOp(self, reverse=reverse)))

    def join(self, separator: StrArg) -> StrRef:
        """Join string elements."""
        from everybase.morphisms import JoinOp
        from everybase.py import StrRef

        return StrRef(JoinOp(self, separator))

    def index(self, value: ElementT) -> IntRef:
        """Find index of value."""
        from everybase.morphisms import IndexOfOp
        from everybase.py import IntRef

        return IntRef(IndexOfOp(self, value))

    def find_index(self, predicate: Callable[[ElementT], bool]) -> IntRef:
        """Find index of first match."""
        from everybase.morphisms import FindIndexOp
        from everybase.py import IntRef

        return IntRef(FindIndexOp(self, predicate))

    def count(self, value: ElementT) -> IntRef:
        """Count occurrences."""
        from everybase.morphisms import CountOp
        from everybase.py import IntRef

        return IntRef(CountOp(self, value))


class Mapping[KeyT, ValueT, ResultT](
    Lengthable,
    Containable[KeyT],
):
    """Combined trait for mapping-like values."""

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
        """Get all keys."""
        from everybase.morphisms.abc_mapping import KeysOp

        return cast("ResultT", self._wrap_keys_result(KeysOp(self)))

    def values_(self) -> ResultT:
        """Get all values."""
        from everybase.morphisms.abc_mapping import ValuesOp

        return cast("ResultT", self._wrap_values_result(ValuesOp(self)))

    def items_(self) -> ResultT:
        """Get all key-value pairs."""
        from everybase.morphisms.abc_mapping import ItemsOp

        return cast("ResultT", self._wrap_items_result(ItemsOp(self)))

    def get_(self, key: KeyT, default: ValueT | None = None) -> ResultT:
        """Get value with default."""
        from everybase.morphisms.abc_mapping import GetOp

        return cast("ResultT", self._wrap_value_result(GetOp(self, key, default)))


class SetLike[ElementT, ResultT](
    Lengthable,
    Containable[ElementT],
):
    """Combined trait for set-like values."""

    def _wrap_set_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate set type."""
        raise NotImplementedError()

    def union(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set union."""
        from everybase.morphisms.abc_set import UnionOp

        return cast("ResultT", self._wrap_set_result(UnionOp(self, other)))

    def intersection(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set intersection."""
        from everybase.morphisms.abc_set import IntersectionOp

        return cast("ResultT", self._wrap_set_result(IntersectionOp(self, other)))

    def difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set difference."""
        from everybase.morphisms.abc_set import DifferenceOp

        return cast("ResultT", self._wrap_set_result(DifferenceOp(self, other)))

    def symmetric_difference(self, other: set[ElementT] | frozenset[ElementT] | Term) -> ResultT:
        """Set symmetric difference."""
        from everybase.morphisms.abc_set import SymmetricDifferenceOp

        return cast("ResultT", self._wrap_set_result(SymmetricDifferenceOp(self, other)))

    def issubset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef:
        """Check if subset."""
        from everybase.morphisms.abc_set import IsSubsetOp
        from everybase.py import BoolRef

        return BoolRef(IsSubsetOp(self, other))

    def issuperset(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef:
        """Check if superset."""
        from everybase.morphisms.abc_set import IsSupersetOp
        from everybase.py import BoolRef

        return BoolRef(IsSupersetOp(self, other))

    def isdisjoint(self, other: set[ElementT] | frozenset[ElementT] | Term) -> BoolRef:
        """Check if disjoint."""
        from everybase.morphisms.abc_set import IsDisjointOp
        from everybase.py import BoolRef

        return BoolRef(IsDisjointOp(self, other))
