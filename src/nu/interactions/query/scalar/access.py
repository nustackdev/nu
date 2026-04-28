"""Collection access ops.

At: Subscript access (seq[key], dict[key])
Slice: Slice access (seq[start:stop:step])
Len: Length (len(obj))
Contains: Containment check (item in container)
"""

from __future__ import annotations

from typing import ClassVar

from nu.terms import BinaryQuery, Mode, ScalarQuery, UnaryQuery


__all__ = [
    "At",
    "Contains",
    "Len",
    "Slice",
]


class Len(UnaryQuery[int]):
    """Length: len(operand)."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, operand: object) -> int:
        """Apply."""
        return len(operand)  # type: ignore


class At[ResultT](BinaryQuery[ResultT]):
    """Subscript access: left[right]."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> ResultT:
        """Apply."""
        return left[right]  # type: ignore


class Slice[ResultT](ScalarQuery[ResultT]):
    """Slice access: operand[start:stop:step]."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, *args: object) -> ResultT:
        """Apply."""
        operand, start, stop, step = args
        return operand[slice(start, stop, step)]  # type: ignore


class Contains(BinaryQuery[bool]):
    """Containment check: right in left."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def apply(self, left: object, right: object) -> bool:
        """Apply."""
        return right in left  # type: ignore
