# ruff: noqa: D102
"""Atomic collection capabilities — protocols + bases.

ContainableProtocol/Base: contains()       — like collections.abc.Container
LengthableProtocol/Base: len_()            — like collections.abc.Sized
IndexableProtocol/Base: __getitem__        — index/key access
SliceableProtocol/Base: slice_()           — slice access
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable


if TYPE_CHECKING:
    from everyabc import IntArg, Term
    from everybase.values import BoolValue, IntValue


__all__ = [
    "ContainableBase",
    "ContainableProtocol",
    "IndexableBase",
    "IndexableProtocol",
    "LengthableBase",
    "LengthableProtocol",
    "SliceableBase",
    "SliceableProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


@runtime_checkable
class ContainableProtocol[ItemT](Protocol):
    """Protocol for values that support containment testing."""

    def contains(self, item: ItemT) -> BoolValue: ...


@runtime_checkable
class LengthableProtocol(Protocol):
    """Protocol for values that have a length."""

    def len_(self) -> IntValue: ...


@runtime_checkable
class IndexableProtocol[KeyT, ResultValue](Protocol):
    """Protocol for values that support index/key access."""

    def __getitem__(self, key: KeyT) -> ResultValue: ...


@runtime_checkable
class SliceableProtocol[ResultT](Protocol):
    """Protocol for values that support slicing."""

    def slice_(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT: ...


# =============================================================================
# BASES
# =============================================================================


class ContainableBase[ItemT]:
    """Base for values that support containment testing."""

    def contains(self, item: ItemT) -> BoolValue:
        """Check if item is in this value."""
        from everybase.morphisms import ContainsOp
        from everybase.values import BoolValue

        return BoolValue(ContainsOp(self, item))


class LengthableBase:
    """Base for values that have a length."""

    def len_(self) -> IntValue:
        """Get length of this value."""
        from everybase.morphisms import LenOp
        from everybase.values import IntValue

        return IntValue(LenOp(self))


class IndexableBase[KeyT, ResultValue]:
    """Base for values that support index/key access."""

    def _wrap_indexable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __getitem__(self, key: KeyT) -> ResultValue:
        """Get item at index/key."""
        from everybase.morphisms import AtOp

        return cast("ResultValue", self._wrap_indexable_result(AtOp(self, key)))


class SliceableBase[ResultT]:
    """Base for values that support slicing."""

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def slice_(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT:
        """Get slice of this value."""
        from everybase.morphisms import SliceOp

        return cast("ResultT", self._wrap_sliceable_result(SliceOp(self, start, stop, step)))
