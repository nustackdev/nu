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
- **higher-order** atoms carry a Nu query child and are dynamic bindings
  (``nu.lang.binding``), exactly like core's ``Map`` / ``Filter``: the child
  is a lambda over what it is handed (the item; the running value and the
  item for ``accumulate``), run once at construction with mem refs. Each run
  pushes one frame and writes the values into it before each evaluation of
  the child. A child given as a plain tree reads nothing.

The frame is the run's own and never reaches the caller, so these atoms are
pure - no ``mutates`` declared.
"""

from __future__ import annotations

import itertools as _it
import operator
from typing import TYPE_CHECKING

from nu.lang import ScalarQuery, StreamQuery
from nu.lang._stream import aiter_any, sync_iter
from nu.lang.binding import _DynamicBinding
from nu.lang.sentinels import UNSET


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Arg, Nu
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
            return _it.repeat(elem, times_t(rt))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        elem_t = children[0]
        times_t = children[1] if len(children) > 1 else None

        async def athunk(rt: Runtime) -> object:
            elem = await elem_t(rt)
            times = None
            if times_t is not None:
                times = await times_t(rt)
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


# --- higher-order (dynamic bindings over a Nu query child) ------------------


class TakeWhile(_DynamicBinding, StreamQuery):
    """``itertools.takewhile(predicate, iterable)`` - yield while the predicate holds.

    Children: ``[source, predicate]``. Each item is written into the run's
    frame, then ``predicate`` runs; the item is yielded while truthy and
    iteration stops at the first falsy result. A NULL result is falsy.
    ``predicate`` is a lambda over the item, or a tree that reads none.

    One frame per run, overwritten per item: work detached from the run (a
    delayed or spawned task, a stream pulled later) reads the latest item,
    not the one current when it started.
    """

    def __init__(self, source: Arg, predicate: Nu | Callable[..., Nu]) -> None:
        super().__init__(source, self._dynamic("TakeWhile", predicate, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate = children
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    binding.write(data, (elem,))
                    if not predicate(inner):
                        return
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
                    if not await predicate(inner):
                        return
                    yield elem

            return agen()

        return athunk


class DropWhile(_DynamicBinding, StreamQuery):
    """``itertools.dropwhile(predicate, iterable)`` - skip while the predicate holds.

    Children: ``[source, predicate]``. Skips items while ``predicate`` is
    truthy; once it is falsy (NULL included), yields that item and every item
    after it with no further predicate evaluation. ``predicate`` is a lambda
    over the item, or a tree that reads none.

    One frame per run, overwritten per item: work detached from the run (a
    delayed or spawned task, a stream pulled later) reads the latest item,
    not the one current when it started.
    """

    def __init__(self, source: Arg, predicate: Nu | Callable[..., Nu]) -> None:
        super().__init__(source, self._dynamic("DropWhile", predicate, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate = children
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            def gen() -> object:
                dropping = True
                for elem in sync_iter(source(rt)):
                    if dropping:
                        binding.write(data, (elem,))
                        if predicate(inner):
                            continue
                        dropping = False
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
                dropping = True
                async for elem in aiter_any(await source(rt)):
                    if dropping:
                        binding.write(data, (elem,))
                        if await predicate(inner):
                            continue
                        dropping = False
                    yield elem

            return agen()

        return athunk


class FilterFalse(_DynamicBinding, StreamQuery):
    """``itertools.filterfalse(predicate, iterable)`` - keep items where the predicate is falsy.

    Children: ``[source, predicate]``. The complement of ``filter``: a NULL
    predicate is falsy, so the item passes. ``predicate`` is a lambda over
    the item, or a tree that reads none.

    One frame per run, overwritten per item: work detached from the run (a
    delayed or spawned task, a stream pulled later) reads the latest item,
    not the one current when it started.
    """

    def __init__(self, source: Arg, predicate: Nu | Callable[..., Nu]) -> None:
        super().__init__(source, self._dynamic("FilterFalse", predicate, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, predicate = children
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    binding.write(data, (elem,))
                    if not predicate(inner):
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
                    if not await predicate(inner):
                        yield elem

            return agen()

        return athunk


class Accumulate(_DynamicBinding, StreamQuery):
    """``itertools.accumulate(iterable, func=None)`` - running accumulation.

    Children: ``[source]`` (plain running sum) or ``[source, func]``. The
    first item is yielded as-is; for each later item the running value and
    the item are written into the run's frame, ``func`` runs, and its result
    is yielded as the new running value. Without ``func`` it sums via
    ``operator.add``. ``func`` is a lambda over the running value and the
    item (it may take only the running value), or a tree that reads none.

    One frame per run, overwritten per step: work detached from the run (a
    delayed or spawned task, a stream pulled later) reads the latest
    accumulator and item, not the ones current when it started.
    """

    def __init__(self, source: Arg, func: Nu | Callable[..., Nu] | None = None) -> None:
        if func is None:
            self._bind_static(None, ())
            super().__init__(source)
        else:
            super().__init__(source, self._dynamic("Accumulate", func, 2))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        func = children[1] if len(children) > 1 else None  # [source, func?]
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

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
                        binding.write(data, (acc, elem))
                        acc = func(inner)
                    yield acc

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        func = children[1] if len(children) > 1 else None  # [source, func?]
        binding = self._binding

        async def athunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

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
                        binding.write(data, (acc, elem))
                        acc = await func(inner)
                    yield acc

            return agen()

        return athunk


class StarMap(_DynamicBinding, StreamQuery):
    """``itertools.starmap(function, iterable)`` - apply ``function`` to unpacked items.

    Children: ``[source, function]``. Each item is a tuple written whole into
    the run's frame. ``function`` is a lambda over the tuple, reading its
    parts by index (``p[0]``, ``p[1]``, ...), or a tree that reads none. The
    result is yielded.

    One frame per run, overwritten per item: work detached from the run (a
    delayed or spawned task, a stream pulled later) reads the latest item,
    not the one current when it started.
    """

    def __init__(self, source: Arg, function: Nu | Callable[..., Nu]) -> None:
        super().__init__(source, self._dynamic("StarMap", function, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, function = children
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            def gen() -> object:
                for elem in sync_iter(source(rt)):
                    binding.write(data, (elem,))
                    yield function(inner)

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source, function = children
        binding = self._binding

        async def athunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            async def agen() -> object:
                async for elem in aiter_any(await source(rt)):
                    binding.write(data, (elem,))
                    yield await function(inner)

            return agen()

        return athunk


class GroupBy(_DynamicBinding, StreamQuery):
    """``itertools.groupby(iterable, key=None)`` - group consecutive items by key.

    Children: ``[source]`` (group by identity) or ``[source, key]``. The key
    function is a lambda over the item, or a tree that reads none. Yields
    ``(key_value, tuple(group))`` for each run of consecutive items sharing
    a key.

    One frame per run, overwritten per item: work detached from the run (a
    delayed or spawned task, a stream pulled later) reads the latest item,
    not the one current when it started.
    """

    def __init__(self, source: Arg, key: Nu | Callable[..., Nu] | None = None) -> None:
        if key is None:
            self._bind_static(None, ())
            super().__init__(source)
        else:
            super().__init__(source, self._dynamic("GroupBy", key, 1))

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        key_fn = children[1] if len(children) > 1 else None  # [source, key?]
        binding = self._binding

        def thunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)

            def keyer(item: object) -> object:
                if key_fn is None:
                    return item
                binding.write(data, (item,))
                return key_fn(inner)

            def gen() -> object:
                for kval, group in _it.groupby(sync_iter(source(rt)), keyer):
                    yield (kval, tuple(group))

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        source = children[0]
        key_fn = children[1] if len(children) > 1 else None  # [source, key?]
        binding = self._binding

        async def athunk(rt: Runtime) -> object:
            inner_ctx, data = binding.frame(rt.ctx)
            inner = rt.on(inner_ctx)
            items = [x async for x in aiter_any(await source(rt))]
            keyed = []
            for item in items:
                if key_fn is None:
                    keyed.append((item, item))
                else:
                    binding.write(data, (item,))
                    keyed.append((await key_fn(inner), item))

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
    a ``ScalarQuery``, surfaced as an ``Object``. The source is materialized so
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
