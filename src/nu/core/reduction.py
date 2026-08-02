"""Reduction atoms: Python's stream-to-scalar builtins.

Maps Python's builtins that fold an iterable down to one value onto Nu
Reductions (a ScalarQuery with a stream child - they bridge the REFUSED cell of
the cardinality matrix by naming the fold). Pure compute over the source.

Builtins covered (Python -> Nu):

- ``sum`` -> ``Sum``, ``min`` -> ``Min``, ``max`` -> ``Max``
- ``any`` -> ``AnyOf``, ``all`` -> ``AllOf``
- ``len`` over a stream -> ``Count``

Plus the structural folds Python reaches for without a single builtin name -
``First`` / ``Last`` / ``Collect`` - the native ways to take the head, the tail,
or the whole drain of a stream.

``functools.reduce`` is stdlib, not a bare builtin, so a generic ``Reduce`` is
core-adjacent (borderline). It is deferred to ``nu.std``, not declared here:
core stays the 1:1 map of native builtins.

Every atom is EVALUABLE: each ``Reduction`` defines ``compile`` (sync) and
``acompile`` (async) returning a thunk that drains its stream child to a scalar,
with EMPTY / INVALID sentinel propagation.

Sorts: all ScalarQuery / Reduction (Q-scalar over Q-stream). Sum, Min, Max,
Any, All and Count are commutative and associative (stream order does not
change the result); Min, Max, Any and All are idempotent too.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Reduction
from nu.lang.sentinels import EMPTY, INVALID

from ._stream import aiter_any, sync_iter


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = [
    "AllOf",
    "AnyOf",
    "Collect",
    "Count",
    "First",
    "Last",
    "Max",
    "Min",
    "Sum",
]


class Sum(Reduction):
    """The sum of every item in its stream child (``sum``)."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            total: object = 0
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                total = total + v
            return total

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            total: object = 0
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                total = total + v
            return total

        return athunk


class Min(Reduction):
    """The smallest item in its stream child (``min``); EMPTY if empty."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")
    _idempotent = Declared(value=True, name="idempotent")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            items = []
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return min(items) if items else EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            items = []
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return min(items) if items else EMPTY

        return athunk


class Max(Reduction):
    """The largest item in its stream child (``max``); EMPTY if empty."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")
    _idempotent = Declared(value=True, name="idempotent")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            items = []
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return max(items) if items else EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            items = []
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return max(items) if items else EMPTY

        return athunk


class AnyOf(Reduction):
    """True if any item in its stream child is truthy (``any``)."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")
    _idempotent = Declared(value=True, name="idempotent")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if v:
                    return True
            return False

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if v:
                    return True
            return False

        return athunk


class AllOf(Reduction):
    """True if every item in its stream child is truthy (``all``)."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")
    _idempotent = Declared(value=True, name="idempotent")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if not v:
                    return False
            return True

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if not v:
                    return False
            return True

        return athunk


class Count(Reduction):
    """The number of items in its stream child (``len`` over a stream)."""

    _commutative = Declared(value=True, name="commutative")
    _associative = Declared(value=True, name="associative")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            n = 0
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                n += 1
            return n

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            n = 0
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                n += 1
            return n

        return athunk


class First(Reduction):
    """The first item of its stream child; EMPTY if the stream is empty."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                return v
            return EMPTY

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                return v
            return EMPTY

        return athunk


class Last(Reduction):
    """The last item of its stream child; EMPTY if the stream is empty."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            last: object = EMPTY
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                last = v
            return last

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            last: object = EMPTY
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                last = v
            return last

        return athunk


class Collect(Reduction):
    """Drain its stream child into one list value."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            out: list = []
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                out.append(v)
            return out

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            out: list = []
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                out.append(v)
            return out

        return athunk
