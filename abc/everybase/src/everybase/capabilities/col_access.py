"""Atomic collection access capabilities.

- Lengthable: len_()
- Indexable: __getitem__
- Sliceable: slice_()
- Containable: contains()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from everyabc import IntArg, Term
    from everybase.py import BoolRef, IntRef


__all__ = [
    "Containable",
    "Indexable",
    "Lengthable",
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
