"""Functional iteration capability.

- Iterable: map_(), filter_(), reduce_(), sum_(), min_(), max_(), any_(), all_()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload


if TYPE_CHECKING:
    from collections.abc import Callable

    from everyabc import Term
    from everybase.py import BoolRef, DictRef, FloatRef, IntRef, ListRef, StrRef


__all__ = [
    "Iterable",
]


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
