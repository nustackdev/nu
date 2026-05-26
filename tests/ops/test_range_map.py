"""Tests for MapRange - query twin of ForRangeDo.

Walks an integer range, evaluates a Nu body query per index, and
yields the flat concatenation of per-step results.
"""

from __future__ import annotations

from nu import (
    Add,
    AttrRef,
    Collect,
    FilterFn,
    Iter,
    Len,
    Literal,
    MapFn,
    MapRange,
    runtime,
)


# ---------------------------------------------------------------------------
# Scalar-yielding body
# ---------------------------------------------------------------------------


async def test_map_range_scalar_body(ctx):
    q = Collect(MapRange(0, 5, body=AttrRef("index")))
    assert await runtime.afirst(q, ctx) == [0, 1, 2, 3, 4]


async def test_map_range_scalar_body_with_transform(ctx):
    q = Collect(MapRange(0, 4, body=Add(AttrRef("index"), Literal(10))))
    assert await runtime.afirst(q, ctx) == [10, 11, 12, 13]


def test_map_range_sync_path(ctx):
    q = Collect(MapRange(0, 3, body=AttrRef("index")))
    assert runtime.first(q, ctx) == [0, 1, 2]


# ---------------------------------------------------------------------------
# Stream-yielding body (flat concat)
# ---------------------------------------------------------------------------


async def test_map_range_stream_body_flat_concat(ctx):
    from nu import At

    rows = [[10, 11], [20, 21], [30, 31]]
    body = Iter(At(Literal(rows), AttrRef("index")))
    q = Collect(MapRange(0, 3, body=body))
    assert await runtime.afirst(q, ctx) == [10, 11, 20, 21, 30, 31]


async def test_map_range_stream_body_with_filterfn(ctx):
    from nu import At

    rows = [[0], [0, 1], [0, 1, 2], [0, 1, 2, 3]]
    body = FilterFn(
        Iter(At(Literal(rows), AttrRef("index"))),
        lambda x: x % 2 == 1,
    )
    q = Collect(MapRange(0, 4, body=body))
    # row 0: [0] -> []
    # row 1: [0,1] -> [1]
    # row 2: [0,1,2] -> [1]
    # row 3: [0,1,2,3] -> [1,3]
    assert await runtime.afirst(q, ctx) == [1, 1, 1, 3]


async def test_map_range_composed_filter_map(ctx):
    # legolas-shaped use case: per index, filter then map.
    from nu import At

    rows = [
        [1, 2],
        [3, 4],
        [5, 6],
    ]
    body = MapFn(
        FilterFn(
            Iter(At(Literal(rows), AttrRef("index"))),
            lambda v: v % 2 == 0,
        ),
        lambda v: v * 100,
    )
    q = Collect(MapRange(0, 3, body=body))
    assert await runtime.afirst(q, ctx) == [200, 400, 600]


# ---------------------------------------------------------------------------
# Empty / edge ranges
# ---------------------------------------------------------------------------


async def test_map_range_empty(ctx):
    q = Collect(MapRange(0, 0, body=AttrRef("index")))
    assert await runtime.afirst(q, ctx) == []


async def test_map_range_start_gt_stop(ctx):
    q = Collect(MapRange(5, 3, body=AttrRef("index")))
    assert await runtime.afirst(q, ctx) == []


async def test_map_range_step(ctx):
    q = Collect(MapRange(0, 10, body=AttrRef("index"), step=3))
    assert await runtime.afirst(q, ctx) == [0, 3, 6, 9]


# ---------------------------------------------------------------------------
# stop accepts a Nu term (e.g. Len)
# ---------------------------------------------------------------------------


async def test_map_range_stop_is_len(ctx):
    data = [10, 20, 30]
    q = Collect(MapRange(0, Len(Literal(data)), body=AttrRef("index")))
    assert await runtime.afirst(q, ctx) == [0, 1, 2]


# ---------------------------------------------------------------------------
# Custom item binding
# ---------------------------------------------------------------------------


async def test_map_range_custom_item_name(ctx):
    q = Collect(MapRange(0, 3, body=AttrRef("range_step"), item="range_step"))
    assert await runtime.afirst(q, ctx) == [0, 1, 2]


# ---------------------------------------------------------------------------
# Async body via MapFn with async transform
# ---------------------------------------------------------------------------


async def test_map_range_async_body(ctx):
    from nu import At

    async def double(x: int) -> int:
        return x * 2

    rows = [[1, 2], [3, 4]]
    body = MapFn(Iter(At(Literal(rows), AttrRef("index"))), double)
    q = Collect(MapRange(0, 2, body=body))
    assert await runtime.afirst(q, ctx) == [2, 4, 6, 8]
