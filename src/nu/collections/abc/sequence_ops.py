"""Sequence ops.

FirstOp, LastOp, IndexOfOp, CountOp
AppendCmd, ExtendCmd, InsertCmd
PopCmd, RemoveValueCmd, ReverseCmd
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence
from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Mode


__all__ = [
    "AppendCmd",
    "CountOp",
    "ExtendCmd",
    "FirstOp",
    "IndexOfOp",
    "InsertCmd",
    "LastOp",
    "PopCmd",
    "RemoveValueCmd",
    "ReverseCmd",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


# =============================================================================
# SEQUENCE READS
# =============================================================================


class FirstOp(ScalarQuery):
    """First element: seq[0]. Returns Invalid if empty."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Sequence):
            raise TypeError(f"first() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[0]


class LastOp(ScalarQuery):
    """Last element: seq[-1]. Returns Invalid if empty."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, Sequence):
            raise TypeError(f"last() requires sequence, got {type(operand).__name__}")
        if len(operand) == 0:
            return INVALID
        return operand[-1]


class IndexOfOp(ScalarQuery):
    """Find index of value: seq.index(value). Returns Invalid if not found."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Sequence):
            raise TypeError(f"index_() requires sequence, got {type(a).__name__}")
        try:
            return a.index(b)
        except ValueError:
            return INVALID


class CountOp(ScalarQuery):
    """Count occurrences: seq.count(value)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, Sequence):
            raise TypeError(f"count_() requires sequence, got {type(a).__name__}")
        return a.count(b)


# =============================================================================
# SEQUENCE MUTATIONS
# =============================================================================


class AppendCmd(ScalarQuery):
    """Append item to end: seq.append(value). Returns None (mutates in-place)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSequence):
            raise TypeError(f"append() requires mutable sequence, got {type(a).__name__}")
        a.append(b)
        return None


class InsertCmd(ScalarQuery):
    """Insert item at index: seq.insert(index, value). Returns None (mutates in-place)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, first: Any, second: Any, third: Any) -> None:  # noqa: ANN401
        super().__init__(first, second, third)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b, c = ops
        if not isinstance(a, MutableSequence):
            raise TypeError(f"insert() requires mutable sequence, got {type(a).__name__}")
        if not isinstance(b, int):
            return INVALID
        a.insert(b, c)
        return None


class PopCmd(ScalarQuery):
    """Pop item at index: seq.pop(index). Returns popped value.

    Default index is -1 (last item).
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSequence):
            raise TypeError(f"pop() requires mutable sequence, got {type(a).__name__}")
        if not isinstance(b, int):
            return INVALID
        try:
            return a.pop(b)
        except IndexError:
            return INVALID


class ExtendCmd(ScalarQuery):
    """Extend sequence with iterable: seq.extend(other). Returns None (mutates in-place)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSequence):
            raise TypeError(f"extend() requires mutable sequence, got {type(a).__name__}")
        if not isinstance(b, Iterable):
            return INVALID
        a.extend(b)
        return None


class RemoveValueCmd(ScalarQuery):
    """Remove first occurrence of value: seq.remove(value). Returns None, or INVALID if not found."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        a, b = ops
        if not isinstance(a, MutableSequence):
            raise TypeError(f"remove() requires mutable sequence, got {type(a).__name__}")
        try:
            a.remove(b)
        except ValueError:
            return INVALID
        return None


class ReverseCmd(ScalarQuery):
    """Reverse sequence in-place: seq.reverse(). Returns None (mutates in-place)."""

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def _apply(self, ctx: Any, ops: list[Any]) -> Any:  # noqa: ANN401
        operand = ops[0]
        if not isinstance(operand, MutableSequence):
            raise TypeError(f"reverse() requires mutable sequence, got {type(operand).__name__}")
        operand.reverse()
        return None
