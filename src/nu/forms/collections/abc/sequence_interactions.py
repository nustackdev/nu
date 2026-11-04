"""Sequence interactions.

Reads (Query): First, Last, IndexOf, Count, Copy
Mutators returning nothing (Command): Append, Extend, Insert,
    RemoveValue, Reverse, Sort, SetIndex, DelIndex
Mutators returning a value (Action): Pop, IAdd, IMul
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.factory import host
from nu.lang import Command, ScalarAction, ScalarQuery
from nu.lang.null import is_null


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


__all__ = [
    "Append",
    "Copy",
    "Count",
    "DelIndex",
    "Extend",
    "First",
    "IAdd",
    "IMul",
    "IndexOf",
    "Insert",
    "Last",
    "ListCreate",
    "ListOf",
    "Pop",
    "RemoveValue",
    "Reverse",
    "SetIndex",
    "Sort",
    "TupleCreate",
    "TupleOf",
]


# =============================================================================
# SEQUENCE CONSTRUCTORS
# =============================================================================

# Empty list: deterministic (always []), but each eval must yield a *fresh*
# mutable object - a future fold/CSE pass must not alias two ListCreate results.
ListCreate = host(list, name="ListCreate")
# Empty tuple: deterministic and immutable (sharing one () is fine).
TupleCreate = host(tuple, name="TupleCreate")
# Tuple from positional items: TupleOf(a, b) evaluates each child expression and
# packs the values into a fresh tuple. Sibling to DictOf.
TupleOf = host(lambda *items: items, name="TupleOf")
# List from positional items: sibling to TupleOf; each eval yields a fresh
# mutable list.
ListOf = host(lambda *items: list(items), name="ListOf")


# =============================================================================
# SEQUENCE READS
# =============================================================================


class First(ScalarQuery):
    """First element: seq[0]."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if not isinstance(obj, Sequence):
                raise TypeError(f"first() requires sequence, got {type(obj).__name__}")
            return obj[0]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if not isinstance(obj, Sequence):
                raise TypeError(f"first() requires sequence, got {type(obj).__name__}")
            return obj[0]

        return athunk


class Last(ScalarQuery):
    """Last element: seq[-1]."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        def thunk(rt: Runtime) -> object:
            obj = operand(rt)
            if not isinstance(obj, Sequence):
                raise TypeError(f"last() requires sequence, got {type(obj).__name__}")
            return obj[-1]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (operand,) = children

        async def athunk(rt: Runtime) -> object:
            obj = await operand(rt)
            if not isinstance(obj, Sequence):
                raise TypeError(f"last() requires sequence, got {type(obj).__name__}")
            return obj[-1]

        return athunk


class IndexOf(ScalarQuery):
    """Find index of value: seq.index(value)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            b = b_t(rt)
            if not isinstance(a, Sequence):
                raise TypeError(f"index_() requires sequence, got {type(a).__name__}")
            return a.index(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            b = await b_t(rt)
            if not isinstance(a, Sequence):
                raise TypeError(f"index_() requires sequence, got {type(a).__name__}")
            return a.index(b)

        return athunk


class Count(ScalarQuery):
    """Count occurrences: seq.count(value)."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            b = b_t(rt)
            if not isinstance(a, Sequence):
                raise TypeError(f"count_() requires sequence, got {type(a).__name__}")
            return a.count(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            b = await b_t(rt)
            if not isinstance(a, Sequence):
                raise TypeError(f"count_() requires sequence, got {type(a).__name__}")
            return a.count(b)

        return athunk


class Copy(ScalarQuery):
    """Shallow copy: list.copy(). Returns a new list; does not mutate."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            return target.copy()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            return target.copy()

        return athunk


# =============================================================================
# SEQUENCE MUTATIONS: Command (mutate, return nothing)
# =============================================================================


class Append(Command):
    """Append item to end: seq.append(value). Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            value = value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            target.append(value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            value = await value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            target.append(value)

        return athunk


class Insert(Command):
    """Insert item at index: seq.insert(index, value). Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, index_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            index = index_t(rt)
            if is_null(index):
                raise ValueError("cannot write with a NULL operand")
            value = value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            if not isinstance(index, int):
                raise TypeError(f"insert() requires int index, got {type(index).__name__}")
            target.insert(index, value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, index_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            index = await index_t(rt)
            if is_null(index):
                raise ValueError("cannot write with a NULL operand")
            value = await value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            if not isinstance(index, int):
                raise TypeError(f"insert() requires int index, got {type(index).__name__}")
            target.insert(index, value)

        return athunk


class Extend(Command):
    """Extend sequence with iterable: seq.extend(other). Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            other = other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target.extend(other)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            other = await other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target.extend(other)

        return athunk


class RemoveValue(Command):
    """Remove first occurrence of value: seq.remove(value). Mutates slot 0; returns nothing.

    ``missing_ok`` is a construction-time flag carried in the payload: when
    set, an absent value is a no-op instead of raising ``ValueError``.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, target: object, value: object, *, missing_ok: bool = False) -> None:
        super().__init__(target, value)
        self._payload = {**self._payload, "missing_ok": missing_ok}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children
        missing_ok = bool(self._payload["missing_ok"])

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            value = value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            if missing_ok and value not in target:
                return
            target.remove(value)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, value_t = children
        missing_ok = bool(self._payload["missing_ok"])

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            value = await value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            if missing_ok and value not in target:
                return
            target.remove(value)

        return athunk


class Reverse(Command):
    """Reverse sequence in-place: seq.reverse(). Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target.reverse()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target.reverse()

        return athunk


class Sort(Command):
    """Sort sequence in-place: list.sort(). Mutates slot 0; returns nothing.

    No-key variant only (key= injection is deferred).
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target.sort()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (target_t,) = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            target.sort()

        return athunk


class SetIndex(Command):
    """Subscript write: seq[index] = value. Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, index_t, value_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            index = index_t(rt)
            if is_null(index):
                raise ValueError("cannot write with a NULL operand")
            value = value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            target[index] = value

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, index_t, value_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            index = await index_t(rt)
            if is_null(index):
                raise ValueError("cannot write with a NULL operand")
            value = await value_t(rt)
            if is_null(value):
                raise ValueError("cannot write with a NULL operand")
            target[index] = value

        return athunk


class DelIndex(Command):
    """Subscript delete: del seq[index]. Mutates slot 0; returns nothing."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, index_t = children

        def thunk(rt: Runtime) -> None:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            index = index_t(rt)
            if is_null(index):
                raise ValueError("cannot write with a NULL operand")
            del target[index]

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, index_t = children

        async def athunk(rt: Runtime) -> None:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            index = await index_t(rt)
            if is_null(index):
                raise ValueError("cannot write with a NULL operand")
            del target[index]

        return athunk


# =============================================================================
# SEQUENCE MUTATIONS: Action (mutate AND return a value)
# =============================================================================


class Pop(ScalarAction):
    """Pop item at index: seq.pop(index). Mutates slot 0 and returns the popped value.

    Default index is -1 (last item).
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        def thunk(rt: Runtime) -> object:
            a = a_t(rt)
            if is_null(a):
                raise ValueError("cannot write with a NULL operand")
            b = b_t(rt)
            if is_null(b):
                raise ValueError("cannot write with a NULL operand")
            return a.pop(b)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        a_t, b_t = children

        async def athunk(rt: Runtime) -> object:
            a = await a_t(rt)
            if is_null(a):
                raise ValueError("cannot write with a NULL operand")
            b = await b_t(rt)
            if is_null(b):
                raise ValueError("cannot write with a NULL operand")
            return a.pop(b)

        return athunk


class IAdd(ScalarAction):
    """In-place concat: seq += other. Mutates slot 0 and returns it (Python __iadd__)."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            other = other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target += other
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, other_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            other = await other_t(rt)
            if is_null(other):
                raise ValueError("cannot write with a NULL operand")
            target += other
            return target

        return athunk


class IMul(ScalarAction):
    """In-place repeat: seq *= n. Mutates slot 0 and returns it (Python __imul__)."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, n_t = children

        def thunk(rt: Runtime) -> object:
            target = target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            n = n_t(rt)
            if is_null(n):
                raise ValueError("cannot write with a NULL operand")
            target *= n
            return target

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        target_t, n_t = children

        async def athunk(rt: Runtime) -> object:
            target = await target_t(rt)
            if is_null(target):
                raise ValueError("cannot write with a NULL operand")
            n = await n_t(rt)
            if is_null(n):
                raise ValueError("cannot write with a NULL operand")
            target *= n
            return target

        return athunk
