# ruff: noqa: D102
"""Sliceable capability."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from nu.terms import IntArg, Nu


__all__ = [
    "SliceableI",
]


class SliceableI[ResultT]:
    """Base for values that support slicing."""

    def _wrap_sliceable_result(self, operand: Nu) -> Nu:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def slice(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT:
        """Get slice of this value."""
        from nu.ops import SliceOp

        return cast("ResultT", self._wrap_sliceable_result(SliceOp(self, start, stop, step)))
