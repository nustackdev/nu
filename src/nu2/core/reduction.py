"""Reduction atoms: Python's stream-to-scalar builtins.

Maps Python's builtins that fold an iterable down to one value onto Nu
Reductions (a ScalarQuery with a stream child - they bridge the REFUSED cell of
the cardinality matrix by naming the fold). Pure compute over the source.

Builtins covered (Python -> Nu):

- ``sum`` -> ``Sum``, ``min`` -> ``Min``, ``max`` -> ``Max``
- ``any`` -> ``Any``, ``all`` -> ``All``
- ``len`` over a stream -> ``Count``

Plus the structural folds Python reaches for without a single builtin name -
``First`` / ``Last`` / ``Collect`` - the native ways to take the head, the tail,
or the whole drain of a stream.

``functools.reduce`` is stdlib, not a bare builtin, so a generic ``Reduce`` is
core-adjacent (borderline). It is deferred to ``nu.std``, not declared here:
core stays the 1:1 map of native builtins.

Every atom is **declared structurally** - a ``Reduction`` subclass with
``Declared`` attrs and no ``compile`` - because a Reduction consumes a stream
child and the stream runtime is not wired yet. They supersede the placeholders
in ``nu2.core._legacy.reductions``; this module is their real home.

Sorts: all ScalarQuery / Reduction (Q-scalar over Q-stream). Sum, Min, Max,
Any, All and Count are commutative and associative (stream order does not
change the result); Min, Max, Any and All are idempotent too.

v1 reference: ``src/nu/queries/reduction.py`` (First, Last, Collect, Reduce),
``reduce.py`` (Sum, MinElem, MaxElem, AnyElem, AllElem), ``iter_reduce.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import Reduction
from nu2.lang.sentinels import EMPTY, INVALID

from ._stream import aiter_any, sync_iter


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = [
    "All",
    "Any",
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


class Min(Reduction):
    """The smallest item in its stream child (``min``)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)


class Max(Reduction):
    """The largest item in its stream child (``max``)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)


class Any(Reduction):
    """True if any item in its stream child is truthy (``any``)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)


class All(Reduction):
    """True if every item in its stream child is truthy (``all``)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)
    idempotent = Declared(value=True)


class Count(Reduction):
    """The number of items in its stream child (``len`` over a stream)."""

    commutative = Declared(value=True)
    associative = Declared(value=True)


class First(Reduction):
    """The first item of its stream child; EMPTY if the stream is empty."""


class Last(Reduction):
    """The last item of its stream child; EMPTY if the stream is empty."""


class Collect(Reduction):
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
