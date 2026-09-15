"""itertools interactions - hand-written stream atoms (hot path, e2e).

Mirrors Python's ``itertools`` 1-1 as ``StreamQuery`` atoms (one ``ScalarQuery``
for ``tee``). Each atom is built directly, like core's ``Map`` / ``Filter``
and ``functools.Reduce`` - no factory. ``StreamQuery`` already declares
sort STREAM_QUERY + cardinality STREAM, so the atoms need no extra attributes.

Two atom shapes:

- **pure combinators** resolve their children, then ``yield from`` the matching
  ``itertools`` call inside a generator. Scalar params (``islice`` bounds,
  ``repeat`` times, ``batched`` n, ``combinations`` r, ``product`` repeat) are
  ordinary children resolved to values before the call. Combinatoric atoms
  materialize their one source with ``list(sync_iter(source(rt)))``.
- **higher-order** atoms carry a Nu query child plus a loop-var-name child
  (default ``"item"``, two names ``"acc"`` / ``"item"`` for ``accumulate``),
  exactly like ``Filter`` / ``Reduce``: bind each item into
  ``rt.ctx.attrs[name]`` (the model's sanctioned loop-var side-channel), then
  evaluate the Nu child. The body reads the item via ``AttrRef("item")``.

The per-item ``ctx.attrs[name] = elem`` write is the loop-var side-channel, not
a tracked fabric write, so these atoms are pure - no ``mutates`` declared.
"""

from __future__ import annotations

import itertools as _it
import operator
from typing import TYPE_CHECKING, cast

from nu.core._stream import aiter_any, sync_iter
from nu.engine import Term
from nu.lang import Literal, ScalarQuery, StreamQuery
from nu.lang.sentinels import EMPTY, INVALID, UNSET


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Arg, Nu, StrArg
    from nu.lang.runtime import Runtime


def _batched(iterable: object, n: int) -> object:
    """Local backport of ``itertools.batched`` (added in Python 3.12)."""
    it = iter(iterable)  # type: ignore[call-overload]
    while batch := tuple(_it.islice(it, n)):
        yield batch


__all__ = [
    "Accumulate",
    "Batched",
    "Chain",
    "ChainFromIterable",
    "Combinations",
    "CombinationsWithReplacement",
    "Compress",
    "Count",
    "Cycle",
    "DropWhile",
    "FilterFalse",
    "GroupBy",
    "Islice",
    "Pairwise",
    "Permutations",
    "Product",
    "Repeat",
    "StarMap",
    "TakeWhile",
    "Tee",
    "ZipLongest",
]


# --- infinite sources -------------------------------------------------------


class Count(StreamQuery):
    """``itertools.count(start, step)`` - an unbounded arithmetic stream.

    Children: ``[start, step]``. Infinite; bound it with ``Islice`` (or any
    short consumer) or it never returns.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start_t, step_t = children

        def thunk(rt: Runtime) -> object:
            return _it.count(start_t(rt), step_t(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        start_t, step_t = children

        async def athunk(rt: Runtime) -> object:
            start = await start_t(rt)
            step = await step_t(rt)

            async def agen() -> object:
                for x in _it.count(start, step):
                    yield x

            return agen()

        return athunk


class Cycle(StreamQuery):
    """``itertools.cycle(iterable)`` - repeat a source forever.

    Children: ``[source]``. Infinite (unless the source is empty).
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                yield from _it.cycle(sync_iter(source(rt)))

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            items = [x async for x in aiter_any(await source(rt))]

            async def agen() -> object:
                for x in _it.cycle(items):
                    yield x

            return agen()

        return athunk


class Repeat(StreamQuery):
    """``itertools.repeat(elem, times)`` - yield ``elem`` ``times`` times (or forever).

    Children: ``[elem]`` or ``[elem, times]``. Without ``times`` it is infinite.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        elem_t = children[0]
        times_t = children[1] if len(children) > 1 else None

        def thunk(rt: Runtime) -> object:
            elem = elem_t(rt)
            if times_t is None:
                return _it.repeat(elem)
            times = times_t(rt)
            if times is EMPTY or times is INVALID:
                return iter(())
            return _it.repeat(elem, times)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        elem_t = children[0]
        times_t = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> object:
            elem = await elem_t(rt)
            times = None
            if times_t is not None:
                times = await times_t(rt)
                if times is EMPTY or times is INVALID:
                    times = 0
            src = _it.repeat(elem) if times is None else _it.repeat(elem, times)

            async def agen() -> object:
                for x in src:
                    yield x

            return agen()

        return athunk


# --- pure combinators -------------------------------------------------------


class Chain(StreamQuery):
    """``itertools.chain(*iterables)`` - concatenate several sources end to end.

    Children: ``[*sources]``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                for src in children:
                    yield from sync_iter(src(rt))

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            async def agen() -> object:
                for src in children:
                    async for x in aiter_any(await src(rt)):
                        yield x

            return agen()

        return athunk


class ChainFromIterable(StreamQuery):
    """``itertools.chain.from_iterable(iterable)`` - flatten one level lazily.

    Children: ``[source]`` where each item of ``source`` is itself iterable.
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


class Islice(StreamQuery):
    """``itertools.islice(iterable, *args)`` - a lazy slice over a source.

    Children: ``[source, *bounds]`` where ``bounds`` is 1-3 ints, read as
    ``stop`` | ``start, stop`` | ``start, stop, step`` (Python's ``islice``).
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        bounds = children[1:]

        def thunk(rt: Runtime) -> object:
            args = [b(rt) for b in bounds]

            def gen() -> object:
                yield from _it.islice(sync_iter(source(rt)), *args)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        bounds = children[1:]

        async def athunk(rt: Runtime) -> object:
            args = [await b(rt) for b in bounds]
            if len(args) == 1:
                start, stop, step = 0, args[0], 1
            elif len(args) == 2:
                start, stop, step = args[0], args[1], 1
            else:
                start, stop, step = args[0], args[1], args[2]
            start = 0 if start is None else start
            step = 1 if step is None else step

            async def agen() -> object:
                # lazy: never drains the source past `stop`, so an infinite
                # source (count/cycle/repeat) is bounded correctly
                target = start
                i = 0
                async for x in aiter_any(await source(rt)):
                    if stop is not None and i >= stop:
                        break
                    if i == target:
                        yield x
                        target += step
                    i += 1

            return agen()

        return athunk


class Compress(StreamQuery):
    """``itertools.compress(data, selectors)`` - keep data where the selector is truthy.

    Children: ``[data, selectors]``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        data, selectors = children

        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                yield from _it.compress(sync_iter(data(rt)), sync_iter(selectors(rt)))

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        data, selectors = children

        async def athunk(rt: Runtime) -> object:
            async def agen() -> object:
                # lazy: walk data and selectors in lockstep, never materialize
                sel = aiter_any(await selectors(rt))
                async for d in aiter_any(await data(rt)):
                    try:
                        s = await sel.__anext__()
                    except StopAsyncIteration:
                        break
                    if s:
                        yield d

            return agen()

        return athunk


class Pairwise(StreamQuery):
    """``itertools.pairwise(iterable)`` - yield overlapping consecutive pairs.

    Children: ``[source]``. ``[a, b, c]`` -> ``(a, b), (b, c)``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        def thunk(rt: Runtime) -> object:
            def gen() -> object:
                yield from _it.pairwise(sync_iter(source(rt)))

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        (source,) = children

        async def athunk(rt: Runtime) -> object:
            async def agen() -> object:
                # lazy: keep only the previous item, never materialize
                prev: object = UNSET
                async for x in aiter_any(await source(rt)):
                    if prev is not UNSET:
                        yield (prev, x)
                    prev = x

            return agen()

        return athunk


class Batched(StreamQuery):
    """``itertools.batched(iterable, n)`` - yield tuples of up to ``n`` items.

    Children: ``[source, n]``. The final batch may be shorter.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, n_t = children

        def thunk(rt: Runtime) -> object:
            n = n_t(rt)

            def gen() -> object:
                yield from _batched(sync_iter(source(rt)), n)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, n_t = children

        async def athunk(rt: Runtime) -> object:
            n = await n_t(rt)
            items = [x async for x in aiter_any(await source(rt))]

            async def agen() -> object:
                for x in _batched(items, n):
                    yield x

            return agen()

        return athunk


class ZipLongest(StreamQuery):
    """``itertools.zip_longest(*iterables, fillvalue=...)`` - zip to the longest.

    Children: ``[*sources, fillvalue]`` (the last child is always the fill
    value). Short sources are padded with ``fillvalue``.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        sources = children[:-1]
        fill_t = children[-1]

        def thunk(rt: Runtime) -> object:
            fill = fill_t(rt)

            def gen() -> object:
                yield from _it.zip_longest(*(sync_iter(s(rt)) for s in sources), fillvalue=fill)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        sources = children[:-1]
        fill_t = children[-1]

        async def athunk(rt: Runtime) -> object:
            fill = await fill_t(rt)
            cols = []
            for s in sources:
                col = [x async for x in aiter_any(await s(rt))]
                cols.append(col)

            async def agen() -> object:
                for x in _it.zip_longest(*cols, fillvalue=fill):
                    yield x

            return agen()

        return athunk


class Product(StreamQuery):
    """``itertools.product(*iterables, repeat=...)`` - the cartesian product.

    Children: ``[*sources, repeat]`` (the last child is always ``repeat``).
    Each source is materialized.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        sources = children[:-1]
        repeat_t = children[-1]

        def thunk(rt: Runtime) -> object:
            repeat = repeat_t(rt)
            pools = [list(sync_iter(s(rt))) for s in sources]

            def gen() -> object:
                yield from _it.product(*pools, repeat=repeat)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        sources = children[:-1]
        repeat_t = children[-1]

        async def athunk(rt: Runtime) -> object:
            repeat = await repeat_t(rt)
            pools = []
            for s in sources:
                pool = [x async for x in aiter_any(await s(rt))]
                pools.append(pool)

            async def agen() -> object:
                for x in _it.product(*pools, repeat=repeat):
                    yield x

            return agen()

        return athunk


class Permutations(StreamQuery):
    """``itertools.permutations(iterable, r)`` - ``r``-length ordered arrangements.

    Children: ``[source]`` or ``[source, r]``. Without ``r`` it uses the full
    length. The source is materialized.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        r_t = children[1] if len(children) > 1 else None

        def thunk(rt: Runtime) -> object:
            pool = list(sync_iter(source(rt)))
            r = None if r_t is None else r_t(rt)

            def gen() -> object:
                yield from _it.permutations(pool, r)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        r_t = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> object:
            pool = [x async for x in aiter_any(await source(rt))]
            r = None if r_t is None else await r_t(rt)

            async def agen() -> object:
                for x in _it.permutations(pool, r):
                    yield x

            return agen()

        return athunk


class Combinations(StreamQuery):
    """``itertools.combinations(iterable, r)`` - ``r``-length sorted subsequences.

    Children: ``[source, r]``. The source is materialized.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, r_t = children

        def thunk(rt: Runtime) -> object:
            pool = list(sync_iter(source(rt)))
            r = r_t(rt)

            def gen() -> object:
                yield from _it.combinations(pool, r)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, r_t = children

        async def athunk(rt: Runtime) -> object:
            pool = [x async for x in aiter_any(await source(rt))]
            r = await r_t(rt)

            async def agen() -> object:
                for x in _it.combinations(pool, r):
                    yield x

            return agen()

        return athunk


class CombinationsWithReplacement(StreamQuery):
    """``itertools.combinations_with_replacement(iterable, r)`` - with repeats allowed.

    Children: ``[source, r]``. The source is materialized.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, r_t = children

        def thunk(rt: Runtime) -> object:
            pool = list(sync_iter(source(rt)))
            r = r_t(rt)

            def gen() -> object:
                yield from _it.combinations_with_replacement(pool, r)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, r_t = children

        async def athunk(rt: Runtime) -> object:
            pool = [x async for x in aiter_any(await source(rt))]
            r = await r_t(rt)

            async def agen() -> object:
                for x in _it.combinations_with_replacement(pool, r):
                    yield x

            return agen()

        return athunk


# --- higher-order (Nu query child + loop-var) -------------------------------


class TakeWhile(StreamQuery):
    """``itertools.takewhile(predicate, iterable)`` - yield while the predicate holds.

    Children: ``[source, predicate, key]``. Each item is bound under the name
    ``key`` yields, then ``predicate`` runs; the item is yielded while truthy
    and iteration stops at the first falsy result. A sentinel predicate stops.
    The body reads the item with ``AttrRef("item")``.
    """

    def __init__(self, source: Arg, predicate: Nu, key: StrArg = "item") -> None:
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
                    if keep is EMPTY or keep is INVALID or not keep:
                        return
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
                    if keep is EMPTY or keep is INVALID or not keep:
                        return
                    yield elem

            return agen()

        return athunk


class DropWhile(StreamQuery):
    """``itertools.dropwhile(predicate, iterable)`` - skip while the predicate holds.

    Children: ``[source, predicate, key]``. Skips items while ``predicate`` is
    truthy; once it is falsy, yields that item and every item after it with no
    further predicate evaluation. The body reads the item via ``AttrRef("item")``.
    """

    def __init__(self, source: Arg, predicate: Nu, key: StrArg = "item") -> None:
        key_node = key if isinstance(key, Term) else Literal(key)
        super().__init__(source, predicate, key_node)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                dropping = True
                for elem in sync_iter(source(rt)):
                    if dropping:
                        rt.ctx.attrs[name] = elem
                        keep = predicate(rt)
                        if keep is not EMPTY and keep is not INVALID and keep:
                            continue
                        dropping = False
                    yield elem

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate, key_t = children

        async def athunk(rt: Runtime) -> object:
            name = await key_t(rt)

            async def agen() -> object:
                dropping = True
                async for elem in aiter_any(await source(rt)):
                    if dropping:
                        rt.ctx.attrs[name] = elem
                        keep = await predicate(rt)
                        if keep is not EMPTY and keep is not INVALID and keep:
                            continue
                        dropping = False
                    yield elem

            return agen()

        return athunk


class FilterFalse(StreamQuery):
    """``itertools.filterfalse(predicate, iterable)`` - keep items where the predicate is falsy.

    Children: ``[source, predicate, key]``. The complement of ``filter``. A
    sentinel predicate skips the item. The body reads it via ``AttrRef("item")``.
    """

    def __init__(self, source: Arg, predicate: Nu, key: StrArg = "item") -> None:
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
                    if not keep:
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
                    if not keep:
                        yield elem

            return agen()

        return athunk


class Accumulate(StreamQuery):
    """``itertools.accumulate(iterable, func=None)`` - running accumulation.

    Children: ``[source]`` (plain running sum) or ``[source, func, acc_key,
    item_key]``. The first item is yielded as-is; each later item binds the
    running value under ``acc_key`` and the item under ``item_key``, evaluates
    ``func``, and yields the new running value. Without ``func`` it sums via
    ``operator.add``. The body reads them via ``AttrRef("acc")`` / ``AttrRef("item")``.
    """

    def __init__(
        self,
        source: Arg,
        func: Nu | None = None,
        acc_key: StrArg = "acc",
        item_key: StrArg = "item",
    ) -> None:
        if func is None:
            super().__init__(source)
            self._payload = {"has_func": False}
        else:
            acc_node = acc_key if isinstance(acc_key, Term) else Literal(acc_key)
            item_node = item_key if isinstance(item_key, Term) else Literal(item_key)
            super().__init__(source, func, acc_node, item_node)
            self._payload = {"has_func": True}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_func = self._payload["has_func"]
        source = children[0]
        func = children[1] if has_func else None
        acc_t = children[2] if has_func else None
        item_t = children[3] if has_func else None

        def thunk(rt: Runtime) -> object:
            acc_name = acc_t(rt) if acc_t is not None else None
            item_name = item_t(rt) if item_t is not None else None

            def gen() -> object:
                started = False
                acc: object = None
                for elem in sync_iter(source(rt)):
                    if not started:
                        acc = elem
                        started = True
                        yield acc
                        continue
                    if func is None:
                        acc = operator.add(acc, elem)
                    else:
                        rt.ctx.attrs[cast("str", acc_name)] = acc
                        rt.ctx.attrs[cast("str", item_name)] = elem
                        acc = func(rt)
                    yield acc

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_func = self._payload["has_func"]
        source = children[0]
        func = children[1] if has_func else None
        acc_t = children[2] if has_func else None
        item_t = children[3] if has_func else None

        async def athunk(rt: Runtime) -> object:
            acc_name = await acc_t(rt) if acc_t is not None else None
            item_name = await item_t(rt) if item_t is not None else None

            async def agen() -> object:
                started = False
                acc: object = None
                async for elem in aiter_any(await source(rt)):
                    if not started:
                        acc = elem
                        started = True
                        yield acc
                        continue
                    if func is None:
                        acc = operator.add(acc, elem)
                    else:
                        rt.ctx.attrs[cast("str", acc_name)] = acc
                        rt.ctx.attrs[cast("str", item_name)] = elem
                        acc = await func(rt)
                    yield acc

            return agen()

        return athunk


class StarMap(StreamQuery):
    """``itertools.starmap(function, iterable)`` - apply ``function`` to unpacked items.

    Children: ``[source, function, key]``. Each item is a tuple bound under
    ``key``; ``function`` reads its parts via ``TupleAttrRef("item")[0]``,
    ``[1]``, ... The result is yielded. A sentinel result is skipped.
    """

    def __init__(self, source: Arg, function: Nu, key: StrArg = "item") -> None:
        key_node = key if isinstance(key, Term) else Literal(key)
        super().__init__(source, function, key_node)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, function, key_t = children

        def thunk(rt: Runtime) -> object:
            name = key_t(rt)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    rt.ctx.attrs[name] = elem
                    result = function(rt)
                    if result is EMPTY or result is INVALID:
                        continue
                    yield result

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, function, key_t = children

        async def athunk(rt: Runtime) -> object:
            name = await key_t(rt)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    rt.ctx.attrs[name] = elem
                    result = await function(rt)
                    if result is EMPTY or result is INVALID:
                        continue
                    yield result

            return agen()

        return athunk


class GroupBy(StreamQuery):
    """``itertools.groupby(iterable, key=None)`` - group consecutive items by key.

    Children: ``[source]`` (group by identity) or ``[source, key, name]``. The
    key function reads the item via ``AttrRef("item")``. Yields ``(key_value,
    tuple(group))`` for each run of consecutive items sharing a key.
    """

    def __init__(self, source: Arg, key: Nu | None = None, name: StrArg = "item") -> None:
        if key is None:
            super().__init__(source)
            self._payload = {"has_key": False}
        else:
            name_node = name if isinstance(name, Term) else Literal(name)
            super().__init__(source, key, name_node)
            self._payload = {"has_key": True}

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_key = self._payload["has_key"]
        source = children[0]
        key_fn = children[1] if has_key else None
        name_t = children[2] if has_key else None

        def thunk(rt: Runtime) -> object:
            name = name_t(rt) if name_t is not None else None

            def keyer(item: object) -> object:
                if key_fn is None:
                    return item
                rt.ctx.attrs[cast("str", name)] = item
                return key_fn(rt)

            def gen() -> object:
                for kval, group in _it.groupby(sync_iter(source(rt)), keyer):
                    yield (kval, tuple(group))

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_key = self._payload["has_key"]
        source = children[0]
        key_fn = children[1] if has_key else None
        name_t = children[2] if has_key else None

        async def athunk(rt: Runtime) -> object:
            name = await name_t(rt) if name_t is not None else None
            items = [x async for x in aiter_any(await source(rt))]
            keyed = []
            for item in items:
                if key_fn is None:
                    keyed.append((item, item))
                else:
                    rt.ctx.attrs[cast("str", name)] = item
                    keyed.append((await key_fn(rt), item))

            async def agen() -> object:
                for kval, group in _it.groupby(keyed, lambda pair: pair[0]):
                    yield (kval, tuple(item for _, item in group))

            return agen()

        return athunk


# --- tee (the lone ScalarQuery) ---------------------------------------------


class Tee(ScalarQuery):
    """``itertools.tee(iterable, n)`` - split a source into ``n`` independent iterators.

    Children: ``[source, n]``. Unlike every other atom here this is NOT a
    stream: it returns a *tuple* of ``n`` iterators (one scalar value), so it is
    a ``ScalarQuery``, surfaced as an ``Any``. The source is materialized so
    the tees are safe to drain in any order.
    """

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, n_t = children

        def thunk(rt: Runtime) -> object:
            n = n_t(rt)
            return tuple(_it.tee(list(sync_iter(source(rt))), n))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, n_t = children

        async def athunk(rt: Runtime) -> object:
            n = await n_t(rt)
            items = [x async for x in aiter_any(await source(rt))]
            return tuple(_it.tee(items, n))

        return athunk
