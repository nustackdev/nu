# ruff: noqa: S311 - seeded Random is exactly what deterministic tests need
"""Functional tests for Kh57ShapesRef — sparse int-keyed map of shapes.

Mirrors :mod:`test_kh57` but for shape-valued kh57 maps: descent to sub-fields
via ``ref[k].field``, sample/range over shape rows, iteration order.
"""

from __future__ import annotations

import random

from nu import Shape, run
from nu.virtuals import FloatRef, IntRef, Kh57ShapesRef, StrRef


class Point(Shape):
    """Row shape stored at each kh57 key."""

    ts_us = IntRef.slot()
    value = FloatRef.slot()
    label = StrRef.slot()


class Series(Shape):
    """Owner shape holding a sparse int-keyed map of Points."""

    name = StrRef.slot()
    points = Kh57ShapesRef.slot(Point)


# ============================================================================
# ROUNDTRIP + FIELD DESCENT
# ============================================================================


def test_store_and_field_descent(ctx) -> None:
    run(Series.points.set({100: {"ts_us": 100, "value": 1.5, "label": "a"}}), ctx)
    assert run(Series.points[100].value, ctx)[0] == 1.5
    assert run(Series.points[100].label, ctx)[0] == "a"
    assert run(Series.points[100].ts_us, ctx)[0] == 100


def test_multiple_shapes_navigate_independently(ctx) -> None:
    run(
        Series.points.set(
            {
                10: {"ts_us": 10, "value": 0.1, "label": "x"},
                20: {"ts_us": 20, "value": 0.2, "label": "y"},
                30: {"ts_us": 30, "value": 0.3, "label": "z"},
            }
        ),
        ctx,
    )
    assert run(Series.points[20].label, ctx)[0] == "y"
    assert run(Series.points[30].value, ctx)[0] == 0.3


def test_field_write_updates_persistently(ctx) -> None:
    run(Series.points.set({42: {"ts_us": 42, "value": 0.0, "label": "orig"}}), ctx)
    run(Series.points[42].label.set("mutated"), ctx)
    assert run(Series.points[42].label, ctx)[0] == "mutated"
    assert run(Series.points[42].ts_us, ctx)[0] == 42


# ============================================================================
# ITERATION IN ORIGINAL KEY ORDER
# ============================================================================


def test_keys_yield_original_int_order(ctx) -> None:
    payload = {
        k: {"ts_us": k, "value": float(k), "label": f"n{k}"} for k in (999, 42, 7, 8000, 100)
    }
    run(Series.points.set(payload), ctx)
    keys = list(run(Series.points.keys(), ctx)[0])
    assert keys == [7, 42, 100, 999, 8000]


# ============================================================================
# SAMPLING
# ============================================================================


def _load_series(ctx, keys) -> None:
    payload = {k: {"ts_us": k, "value": float(k), "label": f"n{k}"} for k in keys}
    run(Series.points.set(payload), ctx)


def test_sample_returns_n_shape_rows(ctx) -> None:
    _load_series(ctx, range(2_000))
    result = run(Series.points.sample(50), ctx)[0]
    assert len(result) == 50
    for k, row in result:
        assert 0 <= k < 2_000
        # kh57.sample() returns raw view rows; subscript to reach the fields
        assert row["ts_us"] == k
        assert row["value"] == float(k)


def test_sample_respects_range(ctx) -> None:
    _load_series(ctx, range(2_000))
    result = run(Series.points.sample(30, begin=500, end=1_000), ctx)[0]
    assert len(result) == 30
    for k, _ in result:
        assert 500 <= k < 1_000


def test_sample_deterministic_with_seeded_rng(ctx) -> None:
    _load_series(ctx, range(1_000))
    from nu.virtuals.interactions.kh57 import Kh57SampleQuery

    q1 = Kh57SampleQuery(Series.points, 25, 0, 1_000, rng=random.Random(7))
    q2 = Kh57SampleQuery(Series.points, 25, 0, 1_000, rng=random.Random(7))
    s1 = run(q1, ctx)[0]
    s2 = run(q2, ctx)[0]
    assert [k for k, _ in s1] == [k for k, _ in s2]


# ============================================================================
# RANGE
# ============================================================================


def test_range_yields_in_key_order(ctx) -> None:
    _load_series(ctx, [500, 100, 300, 200, 400])
    got = list(run(Series.points.range(150, 450), ctx)[0])
    assert [k for k, _ in got] == [200, 300, 400]
    # descend into each row to prove they are real shape views
    for k, row in got:
        assert row["value"] == float(k)


def test_range_empty(ctx) -> None:
    got = list(run(Series.points.range(0, 10), ctx)[0])
    assert got == []
