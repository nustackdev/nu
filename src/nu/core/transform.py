"""Transform atoms: Python's iterable-transforming builtins.

Maps Python's builtins that take an iterable and yield another iterable onto
Nu Queries. Pure shape over their source; effects only ride in through Ref
children.

Builtins covered (Python -> Nu):
- ``map`` -> ``Map``, ``filter`` -> ``Filter``, ``sorted`` -> ``Sorted``

Plus three transforms kept as core: ``SortBy`` (ordered by a key expression),
``Flatten`` (one-level concat) and ``Unique`` (drop already-seen, order
preserved).

``Map``, ``Filter``, ``SortBy``, ``Flatten`` and ``Unique`` are StreamQueries:
stream in, stream out. ``Sorted`` is a ScalarQuery, like Python's ``sorted``:
ordering must see every item before it yields the first, so it takes an
iterable value and yields a list rather than posing as a stream.

``Map``, ``Filter`` and ``SortBy`` bind each item into ``ctx.attrs`` under a
name and evaluate a Nu child against it. The child is usually a lambda over
the item (``lambda x: x > 1``): it runs once, at construction, with a ref to
the item and returns the child tree, and the name is minted for it. Given as a
plain tree instead, the child reads the item with ``Attr(<name>)`` under an
explicit name, itself a **child** (a ``Literal`` or a Ref computed elsewhere,
never an opaque payload). The item is bound with ``ctx.attrs.let`` for the
evaluation of that one item, so it shadows an outer name of the same spelling
and never outlives the item.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.engine import Term
from nu.lang import ScalarQuery, StreamQuery
from nu.lang.literal import Literal
from nu.lang.sentinels import EMPTY

from ._stream import aiter_any, sync_iter


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.context import Attr
    from nu.lang import Arg, Nu, StrArg
    from nu.lang.runtime import Runtime

__all__ = ["Filter", "Flatten", "Map", "SortBy", "Sorted", "Unique"]


class Map(StreamQuery):
    """Applies a query child to every item of a stream child (lazy).

    Args:
        source: the stream to map over.
        transform: evaluated once per item; its value replaces the item. A
            lambda over the item, or a tree reading it with ``Attr(key)``.
        key: name each item is bound under while transform runs, for a tree
            ``transform``. Defaults to ``"item"``; a lambda mints its own.

    Notes:
        - The lambda runs once, at construction, and gets a ref, not a value:
          it builds the tree and never branches on the item in Python.
        - The name belongs to the lambda's code: nested lambdas each get
          their own, while one lambda used again inside its own body
          shadows the outer binding, as with ``nu.let``. An explicit ``key``
          keeps both readable.
        - ``key`` is itself a child (a ``Literal`` or a Ref), not a raw
          string, so it can be computed rather than fixed at write time.
        - The binding lasts for that item's ``transform`` and is released
          before the result is yielded, so it never reaches the consumer.
        - Pulled lazily, one item at a time; nothing runs ahead of the pull.
        - No sentinel check of its own: an EMPTY item, or an EMPTY result
          from ``transform``, passes straight through as a value rather
          than collapsing.

    Yields:
        A stream the same length as ``source`` (stream in, stream out),
        each item ``transform``'s result.

    Example:
        >>> nu.run(nu.Collect(nu.Map(nu.Iter([1, 2, 3]), lambda x: nu.Int(x) + 1)))[0]
        [2, 3, 4]

        The same with an explicit name:

        >>> nu.run(nu.Collect(nu.Map(nu.Iter([1, 2, 3]), nu.Add(nu.Attr("n"), 1), key="n")))[0]
        [2, 3, 4]
    """

    def __init__(
        self,
        source: Arg[Iterable],
        transform: Nu | Callable[[Attr], Nu],
        key: StrArg | None = None,
    ) -> None:
        transform, (key,) = bind("Map", transform, key=key)
        super().__init__(source, transform, "item" if key is None else key)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, transform, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    with rt.ctx.attrs.let(name, elem):
                        result = transform(rt)
                    yield result

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, transform, key_t = children

        async def athunk(rt: Runtime) -> object:
            name = await key_t(rt)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    with rt.ctx.attrs.let(name, elem):
                        result = await transform(rt)
                    yield result

            return agen()

        return athunk


class Filter(StreamQuery):
    """Keeps the items of a stream child for which a predicate holds (lazy).

    Args:
        source: the stream to filter.
        predicate: evaluated once per item; the item passes when this is
            truthy. A lambda over the item, or a tree reading it with
            ``Attr(key)``.
        key: name each item is bound under while predicate runs, for a tree
            ``predicate``. Defaults to ``"item"``; a lambda mints its own.

    Notes:
        - The same scoped binding, and the same lambda form, as :class:`Map`.
        - An EMPTY ``predicate`` result counts as false and drops the item,
          like any falsy value.
        - Pulled lazily, one item at a time.

    Yields:
        A stream no longer than ``source`` (stream in, stream out), holding
        the items where ``predicate`` held.

    Example:
        >>> nu.run(nu.Collect(nu.Filter(nu.Iter([1, 2, 3, 4]), lambda x: x > 2)))[0]
        [3, 4]

        The same with the default name:

        >>> nu.run(nu.Collect(nu.Filter(nu.Iter([1, 2, 3, 4]), nu.Gt(nu.Attr("item"), 2))))[0]
        [3, 4]
    """

    def __init__(
        self,
        source: Arg[Iterable],
        predicate: Nu | Callable[[Attr], Nu],
        key: StrArg | None = None,
    ) -> None:
        predicate, (key,) = bind("Filter", predicate, key=key)
        super().__init__(source, predicate, "item" if key is None else key)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    with rt.ctx.attrs.let(name, elem):
                        keep = predicate(rt)
                    if keep is EMPTY:
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
                    with rt.ctx.attrs.let(name, elem):
                        keep = await predicate(rt)
                    if keep is EMPTY:
                        continue
                    if keep:
                        yield elem

            return agen()

        return athunk


class Sorted(ScalarQuery):
    """Its iterable child collected into an ascending ``list`` (``sorted``).

    Args:
        source: the iterable to sort.

    Notes:
        - Takes an iterable value, like the collection casts. A stream is
          drained into one first with :class:`Collect`.
        - Items must support ordering against each other.
        - An EMPTY item is compared like any other value and raises if it
          can't be ordered against the rest.

    Yields:
        A new list holding every item of ``source``, ascending. EMPTY when
        the child is EMPTY.

    Example:
        >>> nu.run(nu.Sorted([3, 1, 2]))[0]
        [1, 2, 3]

        >>> nu.run(nu.Sorted(nu.Collect(nu.Iter({"b", "a"}))))[0]
        ['a', 'b']
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            v = source(rt)
            if v is EMPTY:
                return EMPTY
            return sorted(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            v = await source(rt)
            if v is EMPTY:
                return EMPTY
            return sorted(v)

        return athunk


class SortBy(StreamQuery):
    """Its source child, ordered by a per-item key expression (eager).

    Args:
        source: the stream to sort.
        key: evaluated once per item to produce its sort key. A lambda over
            the item, like Python's ``sorted(key=...)``, or a tree reading it
            with ``Attr(item)``.
        reverse: descending order when truthy. Defaults to ``False``.
        item: name each item is bound under while ``key`` runs, for a tree
            ``key``. Defaults to ``"item"``; a lambda mints its own.

    Notes:
        - The same scoped binding, and the same lambda form, as
          :class:`Map` / :class:`Filter`.
        - Drains and sorts the whole source before yielding anything, so
          a pull on its output waits for the whole source.

    Yields:
        A stream holding every item of ``source``, ordered by ``key``
        (stream in, stream out).

    Example:
        >>> nu.run(nu.Collect(nu.SortBy(nu.Iter(["bb", "a", "ccc"]), lambda s: nu.Len(s))))[0]
        ['a', 'bb', 'ccc']

        The same with the default name:

        >>> nu.run(nu.Collect(nu.SortBy(nu.Iter(["bb", "a", "ccc"]), nu.Len(nu.Attr("item")))))[0]
        ['a', 'bb', 'ccc']
    """

    def __init__(
        self,
        source: Arg[Iterable],
        key: Nu | Callable[[Attr], Nu],
        reverse: Arg[bool] = False,
        item: StrArg | None = None,
    ) -> None:
        key, (item,) = bind("SortBy", key, item=item)
        reverse_node = reverse if isinstance(reverse, Term) else Literal(reverse)
        super().__init__(source, key, reverse_node, "item" if item is None else item)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, key_expr, reverse_t, item_t = children

        def thunk(rt: Runtime) -> object:
            reverse = bool(reverse_t(rt))
            name = item_t(rt)
            rows: list[tuple[object, object]] = []
            for elem in sync_iter(source(rt)):
                with rt.ctx.attrs.let(name, elem):
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
                with rt.ctx.attrs.let(name, elem):
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
        - No sentinel check of its own: an EMPTY sub-item is treated like
          any other value and raises since it isn't iterable.

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
        - No sentinel check of its own: an EMPTY item is kept like any
          other value and only passes through once.

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
