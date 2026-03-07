"""Collection access morphisms.

AtOp: Subscript access (seq[key], dict[key])
SliceOp: Slice access (seq[start:stop:step])
LenOp: Length (len(obj))
ContainsOp: Containment check (item in container)
"""

from __future__ import annotations

from collections.abc import Container, Mapping, Sequence, Sized

from everybase.core import BinaryOperation, NAryOperation, Sentinel, UnaryOperation


__all__ = [
    "AtOp",
    "ContainsOp",
    "LenOp",
    "SliceOp",
]


class LenOp(UnaryOperation[int]):
    """Length of sequence, mapping, or string: len(obj)."""

    def apply(self, operand: object) -> int:
        """Apply."""
        if not isinstance(operand, Sized):
            raise TypeError(f"len_() requires sized object, got {type(operand).__name__}")
        return len(operand)


class AtOp[ResultT](BinaryOperation[ResultT]):
    """Subscript access: seq[key] or dict[key].

    Returns Invalid for out-of-bounds indices or missing keys.
    """

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        if isinstance(left, Sequence):
            if not isinstance(right, int):
                raise TypeError(f"at() index must be int for sequence, got {type(right).__name__}")
            return left[right]  # type: ignore
        elif isinstance(left, Mapping):
            return left[right]  # type: ignore
        else:
            try:
                return left[right]  # type: ignore
            except TypeError:
                raise TypeError(
                    f"at() requires subscriptable object, got {type(left).__name__}"
                ) from None


class SliceOp[ResultT](NAryOperation[ResultT]):
    """Slice access: seq[start:stop:step]."""

    def apply(self, *args: object) -> ResultT:
        """Apply."""
        operand, start, stop, step = args
        try:
            return operand[slice(start, stop, step)]  # type: ignore
        except TypeError:
            raise TypeError(
                f"slice() requires sliceable object, got {type(operand).__name__}"
            ) from None


class ContainsOp(BinaryOperation[bool]):
    """Containment check: item in container.

    Works for:
    - list/tuple: checks if item is in sequence
    - dict: checks if key is in dict
    - set: checks if item is in set
    - str/bytes: checks if substring is in string
    """

    def apply(self, left: object, right: object) -> bool | Sentinel:
        """Apply."""
        if not isinstance(left, Container):
            raise TypeError(f"contains() requires a container, got {type(left).__name__}")
        return right in left  # type: ignore
