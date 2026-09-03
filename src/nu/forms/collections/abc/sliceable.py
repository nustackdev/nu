"""Sliceable capability.

SliceableForm: values that support slicing.
"""

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
    """Base for values that support slicing.

    Example:
        >>> nu.run(nu.List([1, 2, 3, 4, 5]).slice(1, 4))[0]
        [2, 3, 4]
    """

    def _wrap_sliceable_result(self, operand: Nu) -> Nu:
        """Wrap operand in the subclass's result type.

        Notes:
            - Abstract hook. Every concrete subclass must override this;
              the base raises.
        """
        raise NotImplementedError()

    def slice(
        self, start: IntArg | None, stop: IntArg | None, step: IntArg | None = None
    ) -> ResultT:
        """Slice of self from start to stop, stepping by step.

        Args:
            start: the index to start at, inclusive. None starts from the
                beginning.
            stop: the index to stop at, exclusive. None runs to the end.
            step: the stride between elements. None means every element.

        Notes:
            - Bounds are clamped like Python slicing: an out-of-range start
              or stop never raises.

        Yields:
            The sliced value, wrapped by the subclass. INVALID when self is
            a sentinel.

        Example:
            >>> nu.run(nu.List([1, 2, 3, 4, 5]).slice(1, 4))[0]
            [2, 3, 4]

            >>> nu.run(nu.List([1, 2, 3, 4, 5]).slice(0, 5, 2))[0]
            [1, 3, 5]
        """
        from nu.core import GetItem, Slice

        return cast("ResultT", self._wrap_sliceable_result(GetItem(self, Slice(start, stop, step))))
