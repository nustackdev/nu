"""Collection access ops.

AtOp: Subscript access (seq[key], dict[key])
SliceOp: Slice access (seq[start:stop:step])
LenOp: Length (len(obj))
ContainsOp: Containment check (item in container)
"""

from __future__ import annotations

from nu.terms import BinaryOp, NAryOp, UnaryOp


__all__ = [
    "AtOp",
    "ContainsOp",
    "LenOp",
    "SliceOp",
]


class LenOp(UnaryOp[int]):
    """Length: len(operand)."""

    def apply(self, operand: object) -> int:
        """Apply."""
        return len(operand)  # type: ignore


class AtOp[ResultT](BinaryOp[ResultT]):
    """Subscript access: left[right]."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left[right]  # type: ignore


class SliceOp[ResultT](NAryOp[ResultT]):
    """Slice access: operand[start:stop:step]."""

    def apply(self, *args: object) -> ResultT:
        """Apply."""
        operand, start, stop, step = args
        return operand[slice(start, stop, step)]  # type: ignore


class ContainsOp(BinaryOp[bool]):
    """Containment check: right in left."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return right in left  # type: ignore
