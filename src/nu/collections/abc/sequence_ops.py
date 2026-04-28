"""Sequence ops.

FirstOp, LastOp, IndexOfOp, CountOp
AppendCmd, ExtendCmd, InsertCmd
PopCmd, RemoveValueCmd, ReverseCmd
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence, Sequence
from typing import Any, ClassVar

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.sentinels import INVALID
from nu.terms.types import Effect, Mode


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


class AppendCmd(ScalarCommand):
    """Append item to end: seq.append(value). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        value = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"append() requires mutable sequence, got {type(target).__name__}")
        target.append(value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        value = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"append() requires mutable sequence, got {type(target).__name__}")
        target.append(value)


class InsertCmd(ScalarCommand):
    """Insert item at index: seq.insert(index, value). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, first: Any, second: Any, third: Any) -> None:  # noqa: ANN401
        super().__init__(first, second, third)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        index = runtime.first(self._children[1], ctx)
        value = runtime.first(self._children[2], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"insert() requires mutable sequence, got {type(target).__name__}")
        if not isinstance(index, int):
            raise TypeError(f"insert() requires int index, got {type(index).__name__}")
        target.insert(index, value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        index = await runtime.afirst(self._children[1], ctx)
        value = await runtime.afirst(self._children[2], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"insert() requires mutable sequence, got {type(target).__name__}")
        if not isinstance(index, int):
            raise TypeError(f"insert() requires int index, got {type(index).__name__}")
        target.insert(index, value)


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


class ExtendCmd(ScalarCommand):
    """Extend sequence with iterable: seq.extend(other). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        other = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"extend() requires mutable sequence, got {type(target).__name__}")
        if not isinstance(other, Iterable):
            raise TypeError(f"extend() requires iterable, got {type(other).__name__}")
        target.extend(other)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        other = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"extend() requires mutable sequence, got {type(target).__name__}")
        if not isinstance(other, Iterable):
            raise TypeError(f"extend() requires iterable, got {type(other).__name__}")
        target.extend(other)


class RemoveValueCmd(ScalarCommand):
    """Remove first occurrence of value: seq.remove(value). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, left: Any, right: Any) -> None:  # noqa: ANN401
        super().__init__(left, right)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        value = runtime.first(self._children[1], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"remove() requires mutable sequence, got {type(target).__name__}")
        target.remove(value)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        value = await runtime.afirst(self._children[1], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"remove() requires mutable sequence, got {type(target).__name__}")
        target.remove(value)


class ReverseCmd(ScalarCommand):
    """Reverse sequence in-place: seq.reverse(). Mutates target Ref in-place."""

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, operand: Any) -> None:  # noqa: ANN401
        super().__init__(operand)

    def run(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = runtime.first(self._children[0], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"reverse() requires mutable sequence, got {type(target).__name__}")
        target.reverse()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401
        from nu import runtime

        target = await runtime.afirst(self._children[0], ctx)
        if not isinstance(target, MutableSequence):
            raise TypeError(f"reverse() requires mutable sequence, got {type(target).__name__}")
        target.reverse()
