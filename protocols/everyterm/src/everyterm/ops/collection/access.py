"""Collection access operations.

AtOp: Subscript access (seq[key], dict[key])
SliceOp: Slice access (seq[start:stop:step])
LenOp: Length (len(obj))
ContainsOp: Containment check (item in container)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from everyterm.term import BinaryOp, TernaryOp, UnaryOp
from everyterm.typing import INVALID, Sentinel


if TYPE_CHECKING:
    from everyterm.term import Context, Term


__all__ = [
    "AtOp",
    "ContainsOp",
    "LenOp",
    "SliceOp",
]


class LenOp(UnaryOp[int]):
    """Length of sequence, mapping, or string: len(obj)."""

    def _apply_op(self, operand: object) -> int:
        if not isinstance(operand, (list, tuple, dict, set, frozenset, str, bytes)):
            raise TypeError(f"len_() requires sized object, got {type(operand).__name__}")
        return len(operand)


class AtOp[ResultT](BinaryOp[ResultT | Sentinel]):
    """Subscript access: seq[key] or dict[key].

    Returns Invalid for out-of-bounds indices or missing keys.
    """

    def _apply_op(self, left: object, right: object) -> ResultT | Sentinel:
        if isinstance(left, (list, tuple)):
            if not isinstance(right, int):
                raise TypeError(f"at() index must be int for sequence, got {type(right).__name__}")
            if right < -len(left) or right >= len(left):
                return INVALID
            return left[right]  # type: ignore
        elif isinstance(left, dict):
            if right not in left:
                return INVALID
            return left[right]  # type: ignore
        else:
            try:
                return left[right]  # type: ignore
            except TypeError:
                raise TypeError(
                    f"at() requires subscriptable object, got {type(left).__name__}"
                ) from None


class SliceOp[ResultT](TernaryOp[ResultT]):
    """Slice access: seq[start:stop:step].

    Note: This is modeled as a ternary op for (operand, start, stop).
    Step is stored separately as it's often None.
    """

    def __init__(
        self,
        operand: object,
        start: int | None = None,
        stop: int | None = None,
        step: int | None = None,
    ) -> None:
        """Initialize slice operation.

        Args:
            operand: Sequence to slice
            start: Start index (None = beginning)
            stop: Stop index (None = end)
            step: Step (None = 1)
        """
        # Store as children tuple for consistency, but with placeholder values
        self.children = (cast("Term", operand), cast("Term", start), cast("Term", stop))
        self._start = start
        self._stop = stop
        self._step = step

    def execute(self, context: Context) -> ResultT:
        """Execute slice operation."""
        operand_val = self.children[0].execute(context)
        try:
            return operand_val[self._start : self._stop : self._step]  # type: ignore
        except TypeError:
            raise TypeError(
                f"slice() requires sliceable object, got {type(operand_val).__name__}"
            ) from None

    def _apply_op(self, first: Any, second: Any, third: Any) -> ResultT:  # type: ignore  # noqa: ANN401
        pass

    def __repr__(self) -> str:
        return f"SliceOp({self.children[0]!r}, {self._start}:{self._stop}:{self._step})"


class ContainsOp(BinaryOp[bool]):
    """Containment check: item in container.

    Works for:
    - list/tuple: checks if item is in sequence
    - dict: checks if key is in dict
    - set: checks if item is in set
    - str/bytes: checks if substring is in string
    """

    def _apply_op(self, left: object, right: object) -> bool | Sentinel:
        # left = container, right = item
        if not isinstance(left, (list, tuple, dict, set, frozenset, str, bytes)):
            raise TypeError(
                f"contains() requires list, tuple, dict, set, str, or bytes, "
                f"got {type(left).__name__}"
            )
        return right in left  # type: ignore
