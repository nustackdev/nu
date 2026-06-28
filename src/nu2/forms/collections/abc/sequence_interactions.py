"""Sequence interactions.

Reads (Query): FirstQuery, LastQuery, IndexOfQuery, CountQuery, CopyQuery
Mutators returning nothing (Command): AppendCommand, ExtendCommand, InsertCommand,
    RemoveValueCommand, ReverseCommand, SortCommand, SetIndexCommand, DelIndexCommand
Mutators returning a value (Action): PopAction, IAddAction, IMulAction
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import Command, ScalarAction, ScalarQuery
from nu2.lang.sentinels import EMPTY, INVALID


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime


__all__ = [
    "AppendCommand",
    "CopyQuery",
    "CountQuery",
    "DelIndexCommand",
    "ExtendCommand",
    "FirstQuery",
    "IAddAction",
    "IMulAction",
    "IndexOfQuery",
    "InsertCommand",
    "LastQuery",
    "PopAction",
    "RemoveValueCommand",
    "ReverseCommand",
    "SetIndexCommand",
    "SortCommand",
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


class CopyQuery(ScalarQuery):
    """Shallow copy: list.copy(). Returns a new list; does not mutate."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            return target.copy()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            return target.copy()

        return athunk


# =============================================================================
# SEQUENCE MUTATIONS — Command (mutate, return nothing)
# =============================================================================


class AppendCommand(Command):
    """Append item to end: seq.append(value). Mutates slot 0; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.append(value)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.append(value)

        return athunk


class InsertCommand(Command):
    """Insert item at index: seq.insert(index, value). Mutates slot 0; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            index = index_t(rt)
            if index is EMPTY or index is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            if not isinstance(index, int):
                raise TypeError(f"insert() requires int index, got {type(index).__name__}")
            target.insert(index, value)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            index = await index_t(rt)
            if index is EMPTY or index is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            if not isinstance(index, int):
                raise TypeError(f"insert() requires int index, got {type(index).__name__}")
            target.insert(index, value)

        return athunk


class ExtendCommand(Command):
    """Extend sequence with iterable: seq.extend(other). Mutates slot 0; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target.extend(other)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            other = await other_t(rt)
            if other is EMPTY or other is INVALID:
                return
            target.extend(other)

        return athunk


class RemoveValueCommand(Command):
    """Remove first occurrence of value: seq.remove(value). Mutates slot 0; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.remove(value)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target.remove(value)

        return athunk


class ReverseCommand(Command):
    """Reverse sequence in-place: seq.reverse(). Mutates slot 0; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            target.reverse()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            target.reverse()

        return athunk


class SortCommand(Command):
    """Sort sequence in-place: list.sort(). Mutates slot 0; returns nothing.

    No-key variant only (key= injection is deferred).
    """

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            target.sort()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (target_t,) = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            target.sort()

        return athunk


class SetIndexCommand(Command):
    """Subscript write: seq[index] = value. Mutates slot 0; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            index = index_t(rt)
            if index is EMPTY or index is INVALID:
                return
            value = value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target[index] = value

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            index = await index_t(rt)
            if index is EMPTY or index is INVALID:
                return
            value = await value_t(rt)
            if value is EMPTY or value is INVALID:
                return
            target[index] = value

        return athunk


class DelIndexCommand(Command):
    """Subscript delete: del seq[index]. Mutates slot 0; returns nothing."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            index = index_t(rt)
            if index is EMPTY or index is INVALID:
                return
            del target[index]

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, index_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return
            index = await index_t(rt)
            if index is EMPTY or index is INVALID:
                return
            del target[index]

        return athunk


# =============================================================================
# SEQUENCE MUTATIONS — Action (mutate AND return a value)
# =============================================================================


class PopAction(ScalarAction):
    """Pop item at index: seq.pop(index). Mutates slot 0 and returns the popped value.

    Default index is -1 (last item).
    """

    mutates = Declared(value=frozenset({0}))

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


class IAddAction(ScalarAction):
    """In-place concat: seq += other. Mutates slot 0 and returns it (Python __iadd__)."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            other = other_t(rt)
            if other is EMPTY or other is INVALID:
                return INVALID
            target += other
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
            target += other
            return target

        return athunk


class IMulAction(ScalarAction):
    """In-place repeat: seq *= n. Mutates slot 0 and returns it (Python __imul__)."""

    mutates = Declared(value=frozenset({0}))

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, n_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            n = n_t(rt)
            if n is EMPTY or n is INVALID:
                return INVALID
            target *= n
            return target

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        target_t, n_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if target is EMPTY or target is INVALID:
                return INVALID
            n = await n_t(rt)
            if n is EMPTY or n is INVALID:
                return INVALID
            target *= n
            return target

        return athunk
