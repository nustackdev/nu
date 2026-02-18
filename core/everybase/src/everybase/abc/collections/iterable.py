# ruff: noqa: D102
"""Iterable capability — protocol + base.

IterableProtocol/Base: map_(), filter_(), reduce_(), sum_(), min_(), max_(), any_(), all_()

Type Parameters:
    ElementT: Native Python element type (int, str, dict, etc.)
    CollectionResultT: Wrapped result for collection-level operations
        (map_, filter_ — return collections of the same shape)
    ElementResultT: Wrapped result for element-level operations
        (sum_, min_, max_ — return a single extracted element)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, overload, runtime_checkable


if TYPE_CHECKING:
    from collections.abc import Callable

    from everybase.core import Term

    from ..values import BoolValue, DictValue, FloatValue, IntValue, ListValue, StrValue


__all__ = [
    "IterableBase",
    "IterableProtocol",
]


# =============================================================================
# PROTOCOL
# =============================================================================


@runtime_checkable
class IterableProtocol[ElementT, CollectionResultT, ElementResultT](Protocol):
    """Protocol for values that support functional iteration operations.

    Type Parameters:
        ElementT: Native Python element type (int, str, dict, etc.)
        CollectionResultT: Result type for ops that return collections
            (map_, filter_)
        ElementResultT: Result type for ops that extract single elements
            (sum_, min_, max_)
    """

    def map_[R](self, func: Callable[[ElementT], R]) -> CollectionResultT: ...
    def filter_(self, predicate: Callable[[ElementT], bool]) -> CollectionResultT: ...
    def filter_by_(self, field: object, value: object) -> CollectionResultT: ...
    def reduce_[R](self, func: Callable[[R, ElementT], R], initial: R) -> object: ...
    def pluck_[R](self, field: object) -> CollectionResultT: ...
    def to_dict_[K, V](
        self, key_fn: Callable[[ElementT], K], val_fn: Callable[[ElementT], V]
    ) -> DictValue[K, V]: ...
    def sum_(self) -> ElementResultT: ...
    def min_(self, key: Callable[[ElementT], object] | None = None) -> ElementResultT: ...
    def max_(self, key: Callable[[ElementT], object] | None = None) -> ElementResultT: ...
    def any_(self) -> BoolValue: ...
    def all_(self) -> BoolValue: ...


# =============================================================================
# BASE
# =============================================================================


class IterableBase[ElementT, CollectionResultT, ElementResultT]:
    """Base for values that support functional iteration operations.

    Subclasses must override:
        _wrap_iterable_result(operand) -> CollectionResultT
            Wrap a morphism result in the appropriate collection type.
        _wrap_element_result(operand) -> ElementResultT
            Wrap a morphism result in the appropriate element type.

    Type Parameters:
        ElementT: Native Python element type (int, str, dict, etc.)
        CollectionResultT: Result type for ops that return collections
        ElementResultT: Result type for ops that extract single elements
    """

    def _wrap_iterable_result(self, operand: Term) -> CollectionResultT:
        """Override in subclass to wrap result in appropriate collection type."""
        raise NotImplementedError()

    def _wrap_element_result(self, operand: Term) -> ElementResultT:
        """Override in subclass to wrap result in appropriate element type."""
        raise NotImplementedError()

    def map_[R](self, func: Callable[[ElementT], R]) -> CollectionResultT:
        """Map function over elements."""
        from ..morphisms import MapOp

        return cast("CollectionResultT", self._wrap_iterable_result(MapOp(self, func)))

    def filter_(self, predicate: Callable[[ElementT], bool]) -> CollectionResultT:
        """Filter elements by predicate."""
        from ..morphisms import FilterOp

        return cast("CollectionResultT", self._wrap_iterable_result(FilterOp(self, predicate)))

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
        """Reduce to single value."""
        from ..morphisms import ReduceOp
        from ..values import AnyValue

        return AnyValue(ReduceOp(self, func, initial))

    def sum_(self) -> ElementResultT:
        """Sum all elements."""
        from ..morphisms import SumOp

        return cast("ElementResultT", self._wrap_element_result(SumOp(self)))

    def min_(self, key: Callable[[ElementT], object] | None = None) -> ElementResultT:
        """Get minimum element, optionally by key function."""
        from ..morphisms import MinOp

        return cast("ElementResultT", self._wrap_element_result(MinOp(self, key)))

    def max_(self, key: Callable[[ElementT], object] | None = None) -> ElementResultT:
        """Get maximum element, optionally by key function."""
        from ..morphisms import MaxOp

        return cast("ElementResultT", self._wrap_element_result(MaxOp(self, key)))

    def pluck_(self, field: object) -> CollectionResultT:
        """Extract a field from each element."""
        from ..morphisms import PluckOp

        return cast("CollectionResultT", self._wrap_iterable_result(PluckOp(self, field)))

    def to_dict_[K, V](
        self,
        key_fn: Callable[[ElementT], K],
        val_fn: Callable[[ElementT], V],
    ) -> DictValue[K, V]:
        """Build dict from sequence using key/value extractors."""
        from ..morphisms import ToDictOp
        from ..values import DictValue

        return DictValue(ToDictOp(self, key_fn, val_fn))

    def filter_by_(self, field: object, value: object) -> CollectionResultT:
        """Filter elements where field equals value (both resolved at runtime)."""
        from ..morphisms import FilterByOp

        return cast("CollectionResultT", self._wrap_iterable_result(FilterByOp(self, field, value)))

    def any_(self) -> BoolValue:
        """Check if any element is truthy."""
        from ..morphisms import AnyOp
        from ..values import BoolValue

        return BoolValue(AnyOp(self))

    def all_(self) -> BoolValue:
        """Check if all elements are truthy."""
        from ..morphisms import AllOp
        from ..values import BoolValue

        return BoolValue(AllOp(self))
