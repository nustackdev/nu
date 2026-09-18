"""Iteration atoms: Python's iterator sources and stepping.

Maps Python's builtins that produce or advance iterators onto Nu. Mostly
StreamQuery sources; ``next`` is the odd one - it advances an iterator (mutates
its state) and yields the item, so it is an Action.

Builtins to cover (Python -> Nu):
- sources (Q-stream): ``iter`` -> ``Iter``, ``enumerate`` -> ``Enumerate``,
  ``zip`` -> ``Zip``, ``reversed`` -> ``Reversed``
- stepping (A): ``next`` -> ``Next`` (advance + yield; mutate-and-yield)

Sorts: StreamQuery (Q) for the sources, ScalarAction (A) for ``Next``. Each
source returns an iterator from its thunk (the stream contract); the async twin
returns an async iterator. Lazy lenses (map / filter) live in ``transform``;
folds in ``reduction``.

``range`` is a Python type, not a stream function, so it is a Form (a later
pass), not an atom here; stream a range with ``Iter(<range value>)``. ``Next``
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

__all__ = ["Enumerate", "Iter", "Next", "Reversed", "Zip"]


# --- sources (StreamQuery) -----------------------------------------------


class Iter(StreamQuery):
    """Opens a scalar iterable child into a stream of its elements.

    Args:
        source: the iterable value to open - list, tuple, range, generator,
            dict, set, or anything else Python can iterate.

    Notes:
        - The inverse of a Reduction: a Reduction folds a stream down to a
          scalar, ``Iter`` opens a scalar back up into a stream.

    Yields:
        The elements of ``source``, in iteration order. Lazy: the thunk
        returns an iterator, nothing is pulled until something drains it.

    Example:
        >>> nu.run(nu.Collect(nu.Iter([1, 2, 3])))[0]
        [1, 2, 3]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            return sync_iter(source(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            return aiter_any(await source(rt))

        return athunk


class Enumerate(StreamQuery):
    """Pairs each item of a source child with its running index.

    Args:
        source: the stream to enumerate.
        start: the first index. Optional: leave the child out to start at 0.

    Notes:
        - An EMPTY or INVALID ``start`` collapses the whole result to an
          empty stream rather than raising or falling back to 0.

    Yields:
        ``(index, item)`` tuples, one per item of ``source``, the index
        counting up from ``start`` (Python's ``enumerate``).

    Example:
        >>> nu.run(nu.Collect(nu.Enumerate(nu.Iter(["a", "b"]))))[0]
        [(0, 'a'), (1, 'b')]

        >>> nu.run(nu.Collect(nu.Enumerate(nu.Iter(["a", "b"]), 1)))[0]
        [(1, 'a'), (2, 'b')]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class Zip(StreamQuery):
    """Threads several source children together item by item.

    Args:
        *sources: the streams to zip, one item pulled from each per step.

    Notes:
        - Stops at the shortest source, same as Python's ``zip`` (not the
          ``strict`` variant).
        - No children at all yields an empty stream.

    Yields:
        Tuples of one item per source, in source order.

    Example:
        >>> nu.run(nu.Collect(nu.Zip(nu.Iter([1, 2, 3]), nu.Iter(["a", "b"]))))[0]
        [(1, 'a'), (2, 'b')]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            return zip(*(sync_iter(c(rt)) for c in children), strict=False)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
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


class Reversed(StreamQuery):
    """Yields the items of a source child in reverse order.

    Args:
        source: the stream to reverse.

    Notes:
        - Materializes the whole source before yielding anything, since
          walking backwards needs the full sequence up front - not lazy,
          despite still yielding a stream.

    Yields:
        The items of ``source``, last to first.

    Example:
        >>> nu.run(nu.Collect(nu.Reversed(nu.Iter([1, 2, 3]))))[0]
        [3, 2, 1]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            return reversed(list(sync_iter(source(rt))))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            items = [x async for x in aiter_any(await source(rt))]

            async def agen() -> object:
                for x in reversed(items):
                    yield x

            return agen()

        return athunk


# --- stepping (ScalarAction) ---------------------------------------------


class Next(ScalarAction):
    """Advances a ref-held iterator child and yields the item it pulls.

    Args:
        iterator: the Ref to an iterator held in the Context.

    Notes:
        - Mutates slot 0 (the iterator's position) as well as yielding, so
          ``Next`` is an Action, not a Query - the dual-citizen twin of
          Python's ``next``, and the first concrete Action in core.
        - Structural stub: no ``compile`` yet, waits on the iterator fabric.
          Async twin ``anext`` follows once async sources land.

    Yields:
        The next item pulled from the iterator.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")
