"""Tests for FlatMapFn - flatmap over a stream with a python callable."""

from __future__ import annotations

from nu import (
    Collect,
    FilterFn,
    FlatMapFn,
    Iter,
    MapFn,
    runtime,
)


# ---------------------------------------------------------------------------
# Basic: lambda returns a python list
# ---------------------------------------------------------------------------


async def test_flat_map_fn_basic_list(ctx):
    q = Collect(FlatMapFn(Iter([1, 2, 3]), lambda x: [x, x * 10]))
    assert await runtime.afirst(q, ctx) == [1, 10, 2, 20, 3, 30]


async def test_flat_map_fn_basic_tuple(ctx):
    q = Collect(FlatMapFn(Iter([1, 2]), lambda x: (x, -x)))
    assert await runtime.afirst(q, ctx) == [1, -1, 2, -2]


async def test_flat_map_fn_basic_generator(ctx):
    q = Collect(FlatMapFn(Iter([1, 2, 3]), lambda x: (i for i in range(x))))
    assert await runtime.afirst(q, ctx) == [0, 0, 1, 0, 1, 2]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


async def test_flat_map_fn_empty_source(ctx):
    q = Collect(FlatMapFn(Iter([]), lambda x: [x, x]))
    assert await runtime.afirst(q, ctx) == []


async def test_flat_map_fn_empty_per_step(ctx):
    q = Collect(FlatMapFn(Iter([1, 2, 3]), lambda x: []))
    assert await runtime.afirst(q, ctx) == []


async def test_flat_map_fn_mixed_empty(ctx):
    q = Collect(FlatMapFn(Iter([1, 2, 3]), lambda x: [x] if x % 2 else []))
    assert await runtime.afirst(q, ctx) == [1, 3]


# ---------------------------------------------------------------------------
# Lambda returns a Nu stream query (drained per step)
# ---------------------------------------------------------------------------


async def test_flat_map_fn_nu_stream_body(ctx):
    rows = [[10, 11], [20, 21], [30, 31]]
    q = Collect(FlatMapFn(Iter([0, 1, 2]), lambda i: Iter(rows[i])))
    assert await runtime.afirst(q, ctx) == [10, 11, 20, 21, 30, 31]


async def test_flat_map_fn_nested_filterfn_mapfn(ctx):
    # legolas-shaped use case: per source element, filter then map.
    rows = {
        0: [1, 2, 3, 4],
        1: [5, 6, 7],
        2: [8, 9, 10, 11],
    }
    q = Collect(
        FlatMapFn(
            Iter([0, 1, 2]),
            lambda i: MapFn(
                FilterFn(Iter(rows[i]), lambda v: v % 2 == 0),
                lambda v: v * 100,
            ),
        ),
    )
    # row 0 evens: [2,4] -> [200,400]
    # row 1 evens: [6]   -> [600]
    # row 2 evens: [8,10]-> [800,1000]
    assert await runtime.afirst(q, ctx) == [200, 400, 600, 800, 1000]


# ---------------------------------------------------------------------------
# Composition with other Fn primitives
# ---------------------------------------------------------------------------


async def test_flat_map_fn_after_filter(ctx):
    src = FilterFn(Iter([1, 2, 3, 4, 5]), lambda x: x % 2 == 1)
    q = Collect(FlatMapFn(src, lambda x: [x] * x))
    # 1->[1], 3->[3,3,3], 5->[5,5,5,5,5]
    assert await runtime.afirst(q, ctx) == [1, 3, 3, 3, 5, 5, 5, 5, 5]


async def test_map_fn_over_flat_map_fn(ctx):
    inner = FlatMapFn(Iter([1, 2]), lambda x: [x, x])
    q = Collect(MapFn(inner, lambda x: x + 100))
    assert await runtime.afirst(q, ctx) == [101, 101, 102, 102]


# ---------------------------------------------------------------------------
# Auto-wrap source (scalar iterable without explicit Iter)
# ---------------------------------------------------------------------------


async def test_flat_map_fn_scalar_iterable_source(ctx):
    q = Collect(FlatMapFn([1, 2, 3], lambda x: [x, x]))
    assert await runtime.afirst(q, ctx) == [1, 1, 2, 2, 3, 3]


# ---------------------------------------------------------------------------
# Sync path
# ---------------------------------------------------------------------------


def test_flat_map_fn_sync_path(ctx):
    q = Collect(FlatMapFn(Iter([1, 2, 3]), lambda x: [x, -x]))
    assert runtime.first(q, ctx) == [1, -1, 2, -2, 3, -3]


def test_flat_map_fn_sync_path_with_nu_body(ctx):
    rows = [[1, 2], [3, 4]]
    q = Collect(FlatMapFn(Iter([0, 1]), lambda i: Iter(rows[i])))
    assert runtime.first(q, ctx) == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Async transform
# ---------------------------------------------------------------------------


async def test_flat_map_fn_async_transform(ctx):
    async def expand(x: int) -> list[int]:
        return [x, x * 2]

    q = Collect(FlatMapFn(Iter([1, 2, 3]), expand))
    assert await runtime.afirst(q, ctx) == [1, 2, 2, 4, 3, 6]


async def test_flat_map_fn_async_transform_returns_nu_stream(ctx):
    rows = [[10, 11], [20, 21]]

    async def pick(i: int):
        return Iter(rows[i])

    q = Collect(FlatMapFn(Iter([0, 1]), pick))
    assert await runtime.afirst(q, ctx) == [10, 11, 20, 21]


# ---------------------------------------------------------------------------
# String/bytes treated as scalar (not exploded into characters)
# ---------------------------------------------------------------------------


async def test_flat_map_fn_string_result_kept_whole(ctx):
    q = Collect(FlatMapFn(Iter([1, 2]), lambda x: f"v{x}"))
    assert await runtime.afirst(q, ctx) == ["v1", "v2"]
