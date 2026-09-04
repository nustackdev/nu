"""Transform atoms: Python's stream-to-stream builtins.

Maps Python's builtins that take an iterable and yield another iterable onto Nu
StreamQueries (lazy lenses - pulled per item, no materialization). Pure shape
over their source; effects only ride in through Ref children.

Builtins to cover (Python -> Nu):
- ``map`` -> ``Map``, ``filter`` -> ``Filter``, ``sorted`` -> ``Sorted``

Plus two transforms kept as core: ``Flatten`` (one-level concat) and
``Unique`` (drop already-seen, order preserved).

``Map`` and ``Filter`` bind each item into the attrs side-channel under a name
and evaluate a Nu child against it. The name is a **child** (a Query yielding
the name), so it can be a ``Literal`` or a Ref computed elsewhere - never an
opaque payload. The body reads the item with ``AttrRef(<name>)``. The per-item
binding writes ``ctx.attrs`` directly - the model's side-channel for loop
variables, not a tracked fabric write.

Sorts: all StreamQuery (Q). ``Sorted`` / ``Flatten`` / ``Unique`` stay
structural stubs (no ``compile``) until they are filled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.engine import Term
from nu.lang import StreamQuery
from nu.lang.sentinels import EMPTY, INVALID

from ._stream import aiter_any, sync_iter
from .literal import Literal


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.lang import Arg, Nu, StrArg
    from nu.lang.runtime import Runtime

__all__ = ["Filter", "Flatten", "Map", "SortBy", "Sorted", "Unique"]


class Map(StreamQuery):
    """Applies a query child to every item of a stream child (lazy).

    Args:
        source: the stream to map over.
        transform: evaluated once per item; its value replaces the item.
        key: name each item is bound under while transform runs. Defaults
            to ``"item"``.

    Notes:
        - ``key`` is itself a child (a ``Literal`` or a Ref), not a raw
          string, so it can be computed rather than fixed at write time.
        - ``transform`` reads the item with ``AttrRef(<name>)``. The
          binding writes ``ctx.attrs`` directly - the side-channel for loop
          variables, not a tracked fabric write.
        - Pulled lazily, one item at a time; nothing runs ahead of the pull.
        - No sentinel check of its own: an EMPTY or INVALID item, or an
          EMPTY or INVALID result from ``transform``, passes straight
          through as a value rather than collapsing.

    Yields:
        A stream the same length as ``source`` (stream in, stream out),
        each item ``transform``'s result.

    Example:
        >>> nu.run(nu.Collect(nu.Map(nu.Iter([1, 2, 3]), nu.Add(nu.AttrRef("item"), 1))))[0]
        [2, 3, 4]
    """

    def __init__(self, source: Arg[Iterable], transform: Nu, key: StrArg = "item") -> None:
        key_node = key if isinstance(key, Term) else Literal(key)
        super().__init__(source, transform, key_node)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, transform, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    rt.ctx.attrs[name] = elem
                    yield transform(rt)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, transform, key_t = children

        async def athunk(rt: Runtime) -> object:
            name = await key_t(rt)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    rt.ctx.attrs[name] = elem
                    yield await transform(rt)

            return agen()

        return athunk


class Filter(StreamQuery):
    """Keeps the items of a stream child for which a predicate holds (lazy).

    Args:
        source: the stream to filter.
        predicate: evaluated once per item; the item passes when this is
            truthy.
        key: name each item is bound under while predicate runs. Defaults
            to ``"item"``.

    Notes:
        - ``predicate`` reads the item with ``AttrRef(<name>)``, the same
          side-channel binding as :class:`Map`.
        - An EMPTY or INVALID ``predicate`` result drops the item rather
          than propagating the sentinel; only a genuine falsy value does
          that in Python's ``filter``.
        - Pulled lazily, one item at a time.

    Yields:
        A stream no longer than ``source`` (stream in, stream out), holding
        the items where ``predicate`` held.

    Example:
        >>> nu.run(nu.Collect(nu.Filter(nu.Iter([1, 2, 3, 4]), nu.Gt(nu.AttrRef("item"), 2))))[0]
        [3, 4]
    """

    def __init__(self, source: Arg[Iterable], predicate: Nu, key: StrArg = "item") -> None:
        key_node = key if isinstance(key, Term) else Literal(key)
        super().__init__(source, predicate, key_node)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    rt.ctx.attrs[name] = elem
                    keep = predicate(rt)
                    if keep is EMPTY or keep is INVALID:
                        continue
                    if keep:
                        yield elem

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate, key_t = children

        async def athunk(rt: Runtime) -> object:
            name = await key_t(rt)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    rt.ctx.attrs[name] = elem
                    keep = await predicate(rt)
                    if keep is EMPTY or keep is INVALID:
                        continue
                    if keep:
                        yield elem

            return agen()

        return athunk


class Sorted(StreamQuery):
    """Its source child, ordered (eager).

    Args:
        source: the stream to sort.

    Notes:
        - Drains the whole source before yielding anything - the one
          barrier among these lenses. A pull on its output blocks until
          the whole source is drained and sorted.
        - Items must support ordering against each other.
        - No sentinel check of its own: an EMPTY or INVALID item is
          compared like any other value and raises if it can't be ordered
          against the rest.

    Yields:
        A stream holding every item of ``source``, ascending (stream in,
        stream out).

    Example:
        >>> nu.run(nu.Collect(nu.Sorted(nu.Iter([3, 1, 2]))))[0]
        [1, 2, 3]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            return iter(sorted(sync_iter(source(rt))))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            items = sorted([x async for x in aiter_any(await source(rt))])

            async def agen() -> object:
                for x in items:
                    yield x

            return agen()

        return athunk


class SortBy(StreamQuery):
    """Its source child, ordered by a per-item key expression (eager).

    Args:
        source: the stream to sort.
        key: evaluated once per item to produce its sort key.
        reverse: descending order when truthy. Defaults to ``False``.
        item: name each item is bound under while ``key`` runs. Defaults
            to ``"item"``.

    Notes:
        - ``key`` reads the item with ``AttrRef(<name>)``, the same
          side-channel binding as :class:`Map` / :class:`Filter`.
        - Drains and sorts the whole source before yielding anything, the
          same barrier as :class:`Sorted`.

    Yields:
        A stream holding every item of ``source``, ordered by ``key``
        (stream in, stream out).

    Example:
        >>> nu.run(nu.Collect(nu.SortBy(nu.Iter(["bb", "a", "ccc"]), nu.Len(nu.AttrRef("item")))))[0]
        ['a', 'bb', 'ccc']
    """

    def __init__(
        self,
        source: Arg[Iterable],
        key: Nu,
        reverse: Arg[bool] = False,
        item: StrArg = "item",
    ) -> None:
        reverse_node = reverse if isinstance(reverse, Term) else Literal(reverse)
        item_node = item if isinstance(item, Term) else Literal(item)
        super().__init__(source, key, reverse_node, item_node)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, key_expr, reverse_t, item_t = children

        def thunk(rt: Runtime) -> object:
            reverse = bool(reverse_t(rt))
            name = item_t(rt)
            rows: list[tuple[object, object]] = []
            for elem in sync_iter(source(rt)):
                rt.ctx.attrs[name] = elem
                rows.append((key_expr(rt), elem))
            rows.sort(key=lambda kv: kv[0], reverse=reverse)
            return iter(v for _, v in rows)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, key_expr, reverse_t, item_t = children

        async def athunk(rt: Runtime) -> object:
            reverse = bool(await reverse_t(rt))
            name = await item_t(rt)
            rows: list[tuple[object, object]] = []
            async for elem in aiter_any(await source(rt)):
                rt.ctx.attrs[name] = elem
                rows.append((await key_expr(rt), elem))
            rows.sort(key=lambda kv: kv[0], reverse=reverse)

            async def agen() -> object:
                for _, v in rows:
                    yield v

            return agen()

        return athunk


class Flatten(StreamQuery):
    """Concatenates a source of iterables one level into a flat stream (lazy).

    Args:
        source: the stream of iterables to flatten. Each item must itself
            be iterable.

    Notes:
        - Only one level deep - an item that yields more iterables stays
          nested.
        - No sentinel check of its own: an EMPTY or INVALID sub-item is
          treated like any other value and raises since it isn't iterable.

    Yields:
        A stream of every item from every sub-iterable of ``source``, in
        order (stream in, stream out).

    Example:
        >>> nu.run(nu.Collect(nu.Flatten(nu.Iter([[1, 2], [3], [4, 5]]))))[0]
        [1, 2, 3, 4, 5]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                for sub in sync_iter(source(rt)):
                    yield from sub

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            async def agen() -> object:
                async for sub in aiter_any(await source(rt)):
                    for x in sub:
                        yield x

            return agen()

        return athunk


class Unique(StreamQuery):
    """Yields each item of a source child once, first-seen order (lazy).

    Args:
        source: the stream to dedupe.

    Notes:
        - Items must be hashable.
        - Keeps every distinct item seen so far to check membership, so
          memory grows with the number of distinct items, not the length
          of ``source``.
        - No sentinel check of its own: an EMPTY or INVALID item is kept
          like any other value and only passes through once.

    Yields:
        A stream holding each distinct item of ``source`` once, in
        first-seen order (stream in, stream out).

    Example:
        >>> nu.run(nu.Collect(nu.Unique(nu.Iter([1, 2, 1, 3, 2]))))[0]
        [1, 2, 3]
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                seen: set = set()
                for x in sync_iter(source(rt)):
                    if x not in seen:
                        seen.add(x)
                        yield x

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            async def agen() -> object:
                seen: set = set()
                async for x in aiter_any(await source(rt)):
                    if x not in seen:
                        seen.add(x)
                        yield x

            return agen()

        return athunk
