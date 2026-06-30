"""Reduction atoms: Python's stream-to-scalar builtins.

Maps Python's builtins that fold an iterable down to one value onto Nu
Reductions (a ScalarQuery with a stream child - they bridge the REFUSED cell of
the cardinality matrix by naming the fold). Pure compute over the source.

Builtins covered (Python -> Nu):

- ``sum`` -> ``SumQuery``, ``min`` -> ``MinQuery``, ``max`` -> ``MaxQuery``
- ``any`` -> ``AnyQuery``, ``all`` -> ``AllQuery``
- ``len`` over a stream -> ``CountQuery``

Plus the structural folds Python reaches for without a single builtin name -
``FirstQuery`` / ``LastQuery`` / ``CollectQuery`` - the native ways to take the head, the tail,
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
    "AllQuery",
    "AnyQuery",
    "CollectQuery",
    "CountQuery",
    "FirstQuery",
    "LastQuery",
    "MaxQuery",
    "MinQuery",
    "SumQuery",
]


class SumQuery(Reduction):
    """The sum of every item in its stream child (``sum``)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            total: object = 0
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                total = total + v
            return total

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            total: object = 0
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                total = total + v
            return total

        return athunk


class MinQuery(Reduction):
    """The smallest item in its stream child (``min``); EMPTY if empty."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            items = []
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return min(items) if items else EMPTY

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            items = []
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return min(items) if items else EMPTY

        return athunk


class MaxQuery(Reduction):
    """The largest item in its stream child (``max``); EMPTY if empty."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            items = []
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return max(items) if items else EMPTY

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            items = []
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                items.append(v)
            return max(items) if items else EMPTY

        return athunk


class AnyQuery(Reduction):
    """True if any item in its stream child is truthy (``any``)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if v:
                    return True
            return False

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if v:
                    return True
            return False

        return athunk


class AllQuery(Reduction):
    """True if every item in its stream child is truthy (``all``)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if not v:
                    return False
            return True

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                if not v:
                    return False
            return True

        return athunk


class CountQuery(Reduction):
    """The number of items in its stream child (``len`` over a stream)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            n = 0
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                n += 1
            return n

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            n = 0
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                n += 1
            return n

        return athunk


class FirstQuery(Reduction):
    """The first item of its stream child; EMPTY if the stream is empty."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                return v
            return EMPTY

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                return v
            return EMPTY

        return athunk


class LastQuery(Reduction):
    """The last item of its stream child; EMPTY if the stream is empty."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            last: object = EMPTY
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                last = v
            return last

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            last: object = EMPTY
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                last = v
            return last

        return athunk


class CollectQuery(Reduction):
    """Drain its stream child into one list value."""

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        def thunk(rt: Runtime) -> object:
            out: list = []
            for v in sync_iter(stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                out.append(v)
            return out

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (stream,) = children

        async def athunk(rt: Runtime) -> object:
            out: list = []
            async for v in aiter_any(await stream(rt)):
                if v is EMPTY or v is INVALID:
                    return INVALID
                out.append(v)
            return out

        return athunk
