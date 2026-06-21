"""Sequence interactions.

FirstQuery, LastQuery, IndexOfQuery, CountQuery
AppendQuery, ExtendQuery, InsertQuery
PopQuery, RemoveValueQuery, ReverseQuery
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from nu2.lang import ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "AppendQuery",
    "CountQuery",
    "ExtendQuery",
    "FirstQuery",
    "IndexOfQuery",
    "InsertQuery",
    "LastQuery",
    "PopQuery",
    "RemoveValueQuery",
    "ReverseQuery",
]


# =============================================================================
# SEQUENCE READS
# =============================================================================


class FirstQuery(ScalarQuery):
    """First element: seq[0]. Returns Invalid if empty."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, Sequence):
                raise TypeError(f"first() requires sequence, got {type(obj).__name__}")
            if len(obj) == 0:
                return INVALID
            return obj[0]

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, Sequence):
                raise TypeError(f"first() requires sequence, got {type(obj).__name__}")
            if len(obj) == 0:
                return INVALID
            return obj[0]

        return athunk


class LastQuery(ScalarQuery):
    """Last element: seq[-1]. Returns Invalid if empty."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, Sequence):
                raise TypeError(f"last() requires sequence, got {type(obj).__name__}")
            if len(obj) == 0:
                return INVALID
            return obj[-1]

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if obj is EMPTY or obj is INVALID:
                return INVALID
            if not isinstance(obj, Sequence):
                raise TypeError(f"last() requires sequence, got {type(obj).__name__}")
            if len(obj) == 0:
                return INVALID
            return obj[-1]

        return athunk


class IndexOfQuery(ScalarQuery):
    """Find index of value: seq.index(value). Returns Invalid if not found."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Sequence):
                raise TypeError(f"index_() requires sequence, got {type(a).__name__}")
            try:
                return a.index(b)
            except ValueError:
                return INVALID

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Sequence):
                raise TypeError(f"index_() requires sequence, got {type(a).__name__}")
            try:
                return a.index(b)
            except ValueError:
                return INVALID

        return athunk


class CountQuery(ScalarQuery):
    """Count occurrences: seq.count(value)."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Sequence):
                raise TypeError(f"count_() requires sequence, got {type(a).__name__}")
            return a.count(b)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(a, Sequence):
                raise TypeError(f"count_() requires sequence, got {type(a).__name__}")
            return a.count(b)

        return athunk


# =============================================================================
# SEQUENCE MUTATIONS
# =============================================================================


class AppendQuery(ScalarQuery):
    """Append item to end: seq.append(value); yields the sequence."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.append(value)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.append(value)
            return target

        return athunk


class InsertQuery(ScalarQuery):
    """Insert item at index: seq.insert(index, value); yields the sequence."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t, value_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            index = index_t(rt)
            if index is EMPTY or index is INVALID:
                return INVALID
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            if not isinstance(index, int):
                raise TypeError(f"insert() requires int index, got {type(index).__name__}")
            target.insert(index, value)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t, value_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            index = await index_t(rt)
            if index is EMPTY or index is INVALID:
                return INVALID
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            if not isinstance(index, int):
                raise TypeError(f"insert() requires int index, got {type(index).__name__}")
            target.insert(index, value)
            return target

        return athunk


class PopQuery(ScalarQuery):
    """Pop item at index: seq.pop(index). Returns popped value.

    Default index is -1 (last item).
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(b, int):
                return INVALID
            try:
                return a.pop(b)
            except IndexError:
                return INVALID

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if a is EMPTY or a is INVALID:
                return INVALID
            b = await b_t(rt)
            if b is EMPTY or b is INVALID:
                return INVALID
            if not isinstance(b, int):
                return INVALID
            try:
                return a.pop(b)
            except IndexError:
                return INVALID

        return athunk


class ExtendQuery(ScalarQuery):
    """Extend sequence with iterable: seq.extend(other); yields the sequence."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target.extend(other)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target.extend(other)
            return target

        return athunk


class RemoveValueQuery(ScalarQuery):
    """Remove first occurrence of value: seq.remove(value); yields the sequence."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.remove(value)
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return INVALID
            target.remove(value)
            return target

        return athunk


class ReverseQuery(ScalarQuery):
    """Reverse sequence in-place: seq.reverse(); yields the sequence."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            target.reverse()
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            target.reverse()
            return target

        return athunk
