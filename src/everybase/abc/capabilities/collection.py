# ruff: noqa: D102
"""Atomic collection capabilities — protocols + bases.

IndexableProtocol/Base: __getitem__        — index/key access
SliceableProtocol/Base: slice()            — slice access
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable


if TYPE_CHECKING:
    from everybase.core import IntArg, Term


__all__ = [
    "IndexableBase",
    "IndexableProtocol",
    "SliceableBase",
    "SliceableProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


@runtime_checkable
class IndexableProtocol[KeyT, ResultValue](Protocol):
    """Protocol for values that support index/key access."""

    def __getitem__(self, key: KeyT) -> ResultValue: ...


@runtime_checkable
class SliceableProtocol[ResultT](Protocol):
    """Protocol for values that support slicing."""

    def slice(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT: ...


# =============================================================================
# BASES
# =============================================================================


class IndexableBase[KeyT, ResultValue]:
    """Base for values that support index/key access."""

    def _wrap_indexable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __getitem__(self, key: KeyT) -> ResultValue:
        """Get item at index/key."""
        from ..morphisms import AtOp

        return cast("ResultValue", self._wrap_indexable_result(AtOp(self, key)))


class SliceableBase[ResultT]:
    """Base for values that support slicing."""

    def _wrap_sliceable_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def slice(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT:
        """Get slice of this value."""
        from ..morphisms import SliceOp

        return cast("ResultT", self._wrap_sliceable_result(SliceOp(self, start, stop, step)))
