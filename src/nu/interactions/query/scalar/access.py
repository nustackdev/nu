"""Collection access ops.

At: Subscript access (seq[key], dict[key])
Slice: Slice access (seq[start:stop:step])
Len: Length (len(obj))
Contains: Containment check (item in container)
"""

from __future__ import annotations

from nu.terms import BinaryScalar, NAryScalar, UnaryScalar


__all__ = [
    "At",
    "Contains",
    "Len",
    "Slice",
]


class Len(UnaryScalar[int]):
    """Length: len(operand)."""

    def apply(self, operand: object) -> int:
        """Apply."""
        return len(operand)  # type: ignore


class At[ResultT](BinaryScalar[ResultT]):
    """Subscript access: left[right]."""

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left[right]  # type: ignore


class Slice[ResultT](NAryScalar[ResultT]):
    """Slice access: operand[start:stop:step]."""

    def apply(self, *args: object) -> ResultT:
        """Apply."""
        operand, start, stop, step = args
        return operand[slice(start, stop, step)]  # type: ignore


class Contains(BinaryScalar[bool]):
    """Containment check: right in left."""

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return right in left  # type: ignore
