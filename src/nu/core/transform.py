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

``Map``, ``Filter`` and ``SortBy`` are dynamic bindings (``nu.lang.binding``)
handing each item to a Nu child. The child is a lambda over the item
(``lambda x: x > 1``): it runs once, at construction, with a mem ref to the
item and returns the child tree. Each run pushes one frame and writes the
current item into it before the child is evaluated for that item; the frame
is the run's own and never reaches the caller. A child given as a plain tree
reads no item.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.lang import ScalarQuery, StreamQuery
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.binding import _DynamicBinding


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from nu.lang import Arg, Nu
    from nu.lang.runtime import Runtime

__all__ = ["Filter", "Flatten", "Map", "SortBy", "Sorted", "Unique"]


class Map(_DynamicBinding, StreamQuery):
    """Applies a query child to every item of a stream child (lazy).

    Args:
        source: the stream to map over.
        transform: evaluated once per item; its value replaces the item. A
            lambda over the item, or a tree that reads none.

    Notes:
        - The lambda runs once, at construction, and gets a mem ref, not a
          value: it builds the tree and never branches on the item in Python.
        - The ref's Shape belongs to the lambda's code: nested lambdas each
          get their own, while one lambda used again inside its own body
          shadows the outer binding, as with ``nu.let``.
        - One frame per run, the item written into it before ``transform``
          runs for that item. The frame never reaches the consumer.
        - Work detached from the run (a debounced, delayed or spawned task,
          a stream pulled after the run moved on) reads the latest item,
          not the one current when it started: the run keeps one frame and
          overwrites it per item. Concurrent runs each get their own.
        - Pulled lazily, one item at a time; nothing runs ahead of the pull.
        - No NULL check of its own: a NULL item, or a NULL result from
          ``transform``, passes straight through as a value.

    Yields:
        A stream the same length as ``source`` (stream in, stream out),
        each item ``transform``'s result.

    Example:
        >>> nu.run(nu.Collect(nu.Map(nu.Iter([1, 2, 3]), lambda x: nu.Int(x) + 1)))[0]
        [2, 3, 4]
    """

    def __init__(self, source: Arg[Iterable], transform: Nu | Callable[..., Nu]) -> None:
        super().__init__(source, self._dynamic("Map", transform, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, transform = children
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    binding.write(data, (elem,))
                    yield transform(inner)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, transform = children
        binding = self._binding

        async def athunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    binding.write(data, (elem,))
                    yield await transform(inner)

            return agen()

        return athunk


class Filter(_DynamicBinding, StreamQuery):
    """Keeps the items of a stream child for which a predicate holds (lazy).

    Args:
        source: the stream to filter.
        predicate: evaluated once per item; the item passes when this is
            truthy. A lambda over the item, or a tree that reads none.

    Notes:
        - The same binding, and the same lambda form, as :class:`Map`.
        - Work detached from the run (a debounced, delayed or spawned task,
          a stream pulled after the run moved on) reads the latest item,
          not the one current when it started: the run keeps one frame and
          overwrites it per item. Concurrent runs each get their own.
        - Pulled lazily, one item at a time.

    Yields:
        A stream no longer than ``source`` (stream in, stream out), holding
        the items where ``predicate`` held.

    Example:
        >>> nu.run(nu.Collect(nu.Filter(nu.Iter([1, 2, 3, 4]), lambda x: x > 2)))[0]
        [3, 4]
    """

    def __init__(self, source: Arg[Iterable], predicate: Nu | Callable[..., Nu]) -> None:
        super().__init__(source, self._dynamic("Filter", predicate, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate = children
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    binding.write(data, (elem,))
                    if predicate(inner):
                        yield elem

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate = children
        binding = self._binding

        async def athunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    binding.write(data, (elem,))
                    if await predicate(inner):
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

    Yields:
        A new list holding every item of ``source``, ascending.

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
            return sorted(v)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            v = await source(rt)
            return sorted(v)

        return athunk


class SortBy(_DynamicBinding, StreamQuery):
    """Its source child, ordered by a per-item key expression (eager).

    Args:
        source: the stream to sort.
        key: evaluated once per item to produce its sort key. A lambda over
            the item, like Python's ``sorted(key=...)``, or a tree that
            reads none.
        reverse: descending order when truthy. Defaults to ``False``.

    Notes:
        - The same binding, and the same lambda form, as :class:`Map` /
          :class:`Filter`.
        - Work detached from the run (a debounced, delayed or spawned task,
          a stream pulled after the run moved on) reads the latest item,
          not the one current when it started: the run keeps one frame and
          overwrites it per item. Concurrent runs each get their own.
        - Drains and sorts the whole source before yielding anything, so
          a pull on its output waits for the whole source.

    Yields:
        A stream holding every item of ``source``, ordered by ``key``
        (stream in, stream out).

    Example:
        >>> nu.run(nu.Collect(nu.SortBy(nu.Iter(["bb", "a", "ccc"]), lambda s: nu.Len(s))))[0]
        ['a', 'bb', 'ccc']
    """

    def __init__(
        self,
        source: Arg[Iterable],
        key: Nu | Callable[..., Nu],
        reverse: Arg[bool] = False,
    ) -> None:
        super().__init__(source, self._dynamic("SortBy", key, 1), reverse)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, key_expr, reverse_t = children
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            reverse = bool(reverse_t(rt))
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)
            rows: list[tuple[object, object]] = []
            for elem in sync_iter(source(rt)):
                binding.write(data, (elem,))
                rows.append((key_expr(inner), elem))
            rows.sort(key=lambda kv: kv[0], reverse=reverse)
            return iter(v for _, v in rows)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, key_expr, reverse_t = children
        binding = self._binding

        async def athunk(rt: Runtime) -> object:
            reverse = bool(await reverse_t(rt))
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)
            rows: list[tuple[object, object]] = []
            async for elem in aiter_any(await source(rt)):
                binding.write(data, (elem,))
                rows.append((await key_expr(inner), elem))
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
        - A NULL sub-item raises, since it is not iterable.

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
        - A NULL item is kept like any other value; all NULLs are equal,
          so it passes through once.

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
