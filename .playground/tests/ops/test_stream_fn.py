"""Tests for FilterFn and MapFn - python-callable variants of Filter/Map."""

from __future__ import annotations

from nu import Collect, FilterFn, Iter, MapFn, runtime


# ---------------------------------------------------------------------------
# FilterFn - sync
# ---------------------------------------------------------------------------


async def test_filter_fn_basic(ctx):
    q = Collect(FilterFn(Iter([1, 2, 3, 4, 5]), lambda x: x % 2 == 0))
    assert await runtime.afirst(q, ctx) == [2, 4]


async def test_filter_fn_empty_source(ctx):
    q = Collect(FilterFn(Iter([]), lambda x: True))
    assert await runtime.afirst(q, ctx) == []


async def test_filter_fn_all_filtered_out(ctx):
    q = Collect(FilterFn(Iter([1, 2, 3]), lambda x: False))
    assert await runtime.afirst(q, ctx) == []


async def test_filter_fn_all_kept(ctx):
    q = Collect(FilterFn(Iter([1, 2, 3]), lambda x: True))
    assert await runtime.afirst(q, ctx) == [1, 2, 3]


async def test_filter_fn_on_scalar_iterable(ctx):
    # Auto-wrap: FilterFn accepts a scalar iterable without explicit Iter.
    q = Collect(FilterFn([10, 20, 30, 40], lambda x: x > 15))
    assert await runtime.afirst(q, ctx) == [20, 30, 40]


# ---------------------------------------------------------------------------
# MapFn - sync
# ---------------------------------------------------------------------------


async def test_map_fn_basic(ctx):
    q = Collect(MapFn(Iter([1, 2, 3]), lambda x: x * 10))
    assert await runtime.afirst(q, ctx) == [10, 20, 30]


async def test_map_fn_identity(ctx):
    q = Collect(MapFn(Iter([1, 2, 3]), lambda x: x))
    assert await runtime.afirst(q, ctx) == [1, 2, 3]


async def test_map_fn_empty_source(ctx):
    q = Collect(MapFn(Iter([]), lambda x: x * 2))
    assert await runtime.afirst(q, ctx) == []


async def test_map_fn_change_type(ctx):
    q = Collect(MapFn(Iter([1, 2, 3]), str))
    assert await runtime.afirst(q, ctx) == ["1", "2", "3"]


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


async def test_map_filter_chain(ctx):
    inner = FilterFn(Iter([1, 2, 3, 4, 5]), lambda x: x % 2 == 1)
    q = Collect(MapFn(inner, lambda x: x * x))
    assert await runtime.afirst(q, ctx) == [1, 9, 25]


async def test_filter_map_chain(ctx):
    inner = MapFn(Iter([1, 2, 3, 4]), lambda x: x * 2)
    q = Collect(FilterFn(inner, lambda x: x >= 4))
    assert await runtime.afirst(q, ctx) == [4, 6, 8]


# ---------------------------------------------------------------------------
# Async callables
# ---------------------------------------------------------------------------


async def test_filter_fn_async_predicate(ctx):
    async def is_big(x: int) -> bool:
        return x > 2

    q = Collect(FilterFn(Iter([1, 2, 3, 4]), is_big))
    assert await runtime.afirst(q, ctx) == [3, 4]


async def test_map_fn_async_transform(ctx):
    async def double(x: int) -> int:
        return x * 2

    q = Collect(MapFn(Iter([1, 2, 3]), double))
    assert await runtime.afirst(q, ctx) == [2, 4, 6]


# ---------------------------------------------------------------------------
# Sync-path access via runtime.first
# ---------------------------------------------------------------------------


def test_filter_fn_sync_path(ctx):
    q = Collect(FilterFn(Iter([1, 2, 3, 4]), lambda x: x > 1))
    assert runtime.first(q, ctx) == [2, 3, 4]


def test_map_fn_sync_path(ctx):
    q = Collect(MapFn(Iter([1, 2, 3]), lambda x: x + 100))
    assert runtime.first(q, ctx) == [101, 102, 103]
