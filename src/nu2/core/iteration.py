"""Iteration atoms: Python's iterator sources and stepping.

Maps Python's builtins that produce or advance iterators onto Nu. Mostly
StreamQuery sources; ``next`` is the odd one - it advances an iterator (mutates
its state) and yields the item, so it is an Action.

Builtins to cover (Python -> Nu):
- sources (Q-stream): ``iter`` -> ``Iter``, ``range`` -> ``Range``,
  ``enumerate`` -> ``Enumerate``, ``zip`` -> ``Zip``, ``reversed`` -> ``Reversed``
- stepping (A): ``next`` -> ``Next`` (advance + yield; mutate-and-yield)

Sorts: StreamQuery (Q) for the sources, ScalarAction (A) for ``Next``. Async
twins ``aiter`` / ``anext`` can follow once async sources are needed; note them.
Lazy lenses (map / filter) live in ``transform``; folds in ``reduction``.

These atoms are declared **structurally**: each subclasses the right kind and
carries ``Declared`` attributes only, with no ``compile`` / ``acompile``. The
StreamQuery sources and the one Action all need the fabric/stream runtime that
is not wired yet, so they stand as descriptions the language can attribute and
gate, but not yet evaluate. Behaviour lands when the fabric comes online,
matching the structural pattern in ``_legacy/streams.py`` and
``_legacy/commands.py``.

The placeholder ``Range`` in ``_legacy/streams.py`` is superseded here; this
module is the real home for the iterator sources.

v1 reference: ``src/nu/queries/stream_iter.py``, ``combine.py`` (Zip, Chain,
Enumerate), ``range_map.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu2.engine.structure import Declared
from nu2.lang import ScalarAction, StreamQuery

from ._stream import aiter_any, sync_iter


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu2.lang.runtime import Runtime

__all__ = ["Enumerate", "Iter", "Next", "Reversed", "Zip"]


# --- sources (StreamQuery) -----------------------------------------------


class Iter(StreamQuery):
    """Lifts a scalar iterable child into a stream of its elements.

    Children: ``[source]``. ``source`` is any ScalarQuery whose value is
    iterable (list, tuple, range, generator, dict, set, ...). The inverse of
    a Reduction: where a Reduction folds a stream to a scalar, ``Iter`` opens
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


class Enumerate(StreamQuery):
    """Pairs each item of a stream child with its running index.

    Children: ``[source, start]``. Yields ``(index, item)`` tuples, the index
    counting up from ``start`` (Python's ``enumerate``).
    """


class Zip(StreamQuery):
    """Threads several stream children together item by item.

    Children: ``[*sources]``. Yields tuples of one item per source, stopping
    with the shortest (Python's ``zip``).
    """


class Reversed(StreamQuery):
    """Yields the items of a stream child in reverse order.

    Children: ``[source]``. The stream-shaped twin of Python's ``reversed``;
    it materializes the source to walk it backwards.
    """


# --- stepping (ScalarAction) ---------------------------------------------


class Next(ScalarAction):
    """Advances an iterator child and yields the next item.

    Children: ``[iterator]`` where slot 0 holds the Ref to an iterator in the
    Context. Stepping mutates that iterator's position, so ``Next`` is an
    Action, not a Query: it both writes (slot 0) and yields the item it
    pulled. The dual-citizen twin of Python's ``next``; the first concrete
    Action in core. Async twin ``anext`` follows with async sources.
    """

    mutates = Declared(value=frozenset({0}))
