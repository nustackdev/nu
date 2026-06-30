"""Iteration atoms: Python's iterator sources and stepping.

Maps Python's builtins that produce or advance iterators onto Nu. Mostly
StreamQuery sources; ``next`` is the odd one - it advances an iterator (mutates
its state) and yields the item, so it is an Action.

Builtins to cover (Python -> Nu):
- sources (Q-stream): ``iter`` -> ``IterQuery``, ``enumerate`` -> ``EnumerateQuery``,
  ``zip`` -> ``ZipQuery``, ``reversed`` -> ``ReversedQuery``
- stepping (A): ``next`` -> ``NextAction`` (advance + yield; mutate-and-yield)

Sorts: StreamQuery (Q) for the sources, ScalarAction (A) for ``Next``. Each
source returns an iterator from its thunk (the stream contract); the async twin
returns an async iterator. Lazy lenses (map / filter) live in ``transform``;
folds in ``reduction``.

``range`` is a Python type, not a stream function, so it is a Form (a later
pass), not an atom here; stream a range with ``IterQuery(<range value>)``. ``NextAction``
steps a ref-held iterator, so it stays a structural stub until the iterator
fabric lands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction, StreamQuery
from nu.lang.sentinels import EMPTY, INVALID

from ._stream import aiter_any, sync_iter


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["EnumerateQuery", "IterQuery", "NextAction", "ReversedQuery", "ZipQuery"]


# --- sources (StreamQuery) -----------------------------------------------


class IterQuery(StreamQuery):
    """Lifts a scalar iterable child into a stream of its elements.

    Children: ``[source]``. ``source`` is any ScalarQuery whose value is
    iterable (list, tuple, range, generator, dict, set, ...). The inverse of
    a Reduction: where a Reduction folds a stream to a scalar, ``IterQuery`` opens
    a scalar iterable into a stream. A stream atom's thunk returns an iterator.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        def thunk(rt: Runtime) -> object:
            return sync_iter(source(rt))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            return aiter_any(await source(rt))

        return athunk


class EnumerateQuery(StreamQuery):
    """Pairs each item of a source child with its running index.

    Children: ``[source]`` or ``[source, start]``. Yields ``(index, item)``
    tuples, the index counting up from ``start`` (default 0), Python's
    ``enumerate``.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source = children[0]
        start = children[1] if len(children) > 1 else None

        def thunk(rt: Runtime) -> object:
            if start is None:
                return enumerate(sync_iter(source(rt)))
            s = start(rt)
            if s is EMPTY or s is INVALID:
                return iter(())
            return enumerate(sync_iter(source(rt)), s)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        source = children[0]
        start = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> object:
            begin = 0
            if start is not None:
                s = await start(rt)
                if s is EMPTY or s is INVALID:
                    return aiter_any(())
                begin = s
            src = await source(rt)

            async def agen() -> object:
                i = begin
                async for item in aiter_any(src):
                    yield (i, item)
                    i += 1

            return agen()

        return athunk


class ZipQuery(StreamQuery):
    """Threads several source children together item by item.

    Children: ``[*sources]``. Yields tuples of one item per source, stopping
    with the shortest (Python's ``zip``).
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        def thunk(rt: Runtime) -> object:
            return zip(*(sync_iter(c(rt)) for c in children), strict=False)

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        async def athunk(rt: Runtime) -> object:
            aiters = [aiter_any(await c(rt)) for c in children]

            async def agen() -> object:
                while True:
                    row = []
                    for ai in aiters:
                        try:
                            row.append(await ai.__anext__())
                        except StopAsyncIteration:
                            return
                    yield tuple(row)

            return agen()

        return athunk


class ReversedQuery(StreamQuery):
    """Yields the items of a source child in reverse order.

    Children: ``[source]``. The stream-shaped twin of Python's ``reversed``;
    it materializes the source to walk it backwards.
    """

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        def thunk(rt: Runtime) -> object:
            return reversed(list(sync_iter(source(rt))))

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:  # noqa: D102
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            items = [x async for x in aiter_any(await source(rt))]

            async def agen() -> object:
                for x in reversed(items):
                    yield x

            return agen()

        return athunk


# --- stepping (ScalarAction) ---------------------------------------------


class NextAction(ScalarAction):
    """Advances an iterator child and yields the next item.

    Children: ``[iterator]`` where slot 0 holds the Ref to an iterator in the
    Context. Stepping mutates that iterator's position, so ``NextAction`` is an
    Action, not a Query: it both writes (slot 0) and yields the item it
    pulled. The dual-citizen twin of Python's ``next``; the first concrete
    Action in core. Async twin ``anext`` follows with async sources.
    """

    mutates = Declared(value=frozenset({0}))
