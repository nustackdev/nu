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

    from everyabc import Term
    from everybase.values import BoolValue, DictValue, FloatValue, IntValue, ListValue, StrValue


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
    def reduce_[R](self, func: Callable[[R, ElementT], R], initial: R) -> object: ...
    def sum_(self) -> ElementResultT: ...
    def min_(self) -> ElementResultT: ...
    def max_(self) -> ElementResultT: ...
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
        from everybase.morphisms import MapOp

        return cast("CollectionResultT", self._wrap_iterable_result(MapOp(self, func)))

    def filter_(self, predicate: Callable[[ElementT], bool]) -> CollectionResultT:
        """Filter elements by predicate."""
        from everybase.morphisms import FilterOp

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
        from everybase.morphisms import ReduceOp
        from everybase.values import AnyValue

        return AnyValue(ReduceOp(self, func, initial))

    def sum_(self) -> ElementResultT:
        """Sum all elements."""
        from everybase.morphisms import SumOp

        return cast("ElementResultT", self._wrap_element_result(SumOp(self)))

    def min_(self) -> ElementResultT:
        """Get minimum element."""
        from everybase.morphisms import MinOp

        return cast("ElementResultT", self._wrap_element_result(MinOp(self)))

    def max_(self) -> ElementResultT:
        """Get maximum element."""
        from everybase.morphisms import MaxOp

        return cast("ElementResultT", self._wrap_element_result(MaxOp(self)))

    def any_(self) -> BoolValue:
        """Check if any element is truthy."""
        from everybase.morphisms import AnyOp
        from everybase.values import BoolValue

        return BoolValue(AnyOp(self))

    def all_(self) -> BoolValue:
        """Check if all elements are truthy."""
        from everybase.morphisms import AllOp
        from everybase.values import BoolValue

        return BoolValue(AllOp(self))
