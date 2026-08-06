"""Sliceable capability."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, cast

from nu.lang import Form


if TYPE_CHECKING:
    from nu.lang import IntArg, Nu


__all__ = [
    "SliceableForm",
]


ResultT = TypeVar("ResultT")


class SliceableForm(Form, Generic[ResultT]):
    """Base for values that support slicing."""

    def _wrap_sliceable_result(self, operand: Nu) -> Nu:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def slice(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT:
        """Get slice of this value."""
        from nu.core import GetItem, Slice

        return cast("ResultT", self._wrap_sliceable_result(GetItem(self, Slice(start, stop, step))))
