# ruff: noqa: S311 - seeded Random is exactly what deterministic tests need
"""Functional tests for Kh57Ref — sparse int-keyed map with range sampling.

Verifies:
- Roundtrip put/get/delete through the ref.
- Iteration in original int-key order.
- .sample() returns n items, deterministic with seeded rng, respects range.
- Stability under append outside the queried range.
- .range() yields items in ascending int-key order.
- Lazy/eager facet switching.
"""

from __future__ import annotations

import random

from nu import LiteralQuery, Shape, run
from nu.virtuals import IntRef, Kh57Ref
from nu.virtuals.refs.base import Facet


class Ledger(Shape):
    height = IntRef.slot()
    entries = Kh57Ref.slot(int)  # int-keyed, int-valued kh57 map


# ============================================================================
# ROUNDTRIP
# ============================================================================


def test_put_get(ctx) -> None:
    run(Ledger.entries.set(42, 100), ctx)
    assert run(Ledger.entries.get(42), ctx)[0] == 100


def test_delete(ctx) -> None:
    run(Ledger.entries.set(7, 700), ctx)
    assert run(Ledger.entries.get(7), ctx)[0] == 700
    run(Ledger.entries.delete(7), ctx)
    got = run(Ledger.entries.get(7, LiteralQuery(-1)), ctx)[0]
    assert got == -1


def test_len_contains(ctx) -> None:
    for k in (1, 42, 999, 8000):
        run(Ledger.entries.set(k, k * 10), ctx)
    assert run(Ledger.entries.len(), ctx)[0] == 4
    assert run(Ledger.entries.contains(42), ctx)[0] is True
    assert run(Ledger.entries.contains(3), ctx)[0] is False


# ============================================================================
# ITERATION IN ORIGINAL KEY ORDER
# ============================================================================


def test_iteration_original_order(ctx) -> None:
    # Insert in scrambled order; iteration should yield ascending int keys.
    for k in (999, 42, 7, 8000, 100):
        run(Ledger.entries.set(k, str(k)), ctx)
    keys = list(run(Ledger.entries.keys(), ctx)[0])
    assert keys == [7, 42, 100, 999, 8000]


# ============================================================================
# SAMPLING
# ============================================================================


def _load_range(ctx, keys) -> None:
    for k in keys:
        run(Ledger.entries.set(k, k * 2), ctx)


def test_sample_returns_n(ctx) -> None:
    _load_range(ctx, range(10_000))
    result = run(Ledger.entries.sample(100), ctx)[0]
    assert len(result) == 100
    assert all(0 <= k < 10_000 for k, _ in result)
    assert all(v == k * 2 for k, v in result)


def test_sample_respects_range(ctx) -> None:
    _load_range(ctx, range(10_000))
    result = run(Ledger.entries.sample(50, begin=2_000, end=3_000), ctx)[0]
    assert len(result) == 50
    assert all(2_000 <= k < 3_000 for k, _ in result)


def test_sample_deterministic_with_seeded_rng(ctx) -> None:
    _load_range(ctx, range(5_000))
    from nu.virtuals.interactions.kh57 import Kh57SampleQuery

    q1 = Kh57SampleQuery(Ledger.entries, 100, 0, 5_000, rng=random.Random(42))
    q2 = Kh57SampleQuery(Ledger.entries, 100, 0, 5_000, rng=random.Random(42))
    s1 = run(q1, ctx)[0]
    s2 = run(q2, ctx)[0]
    assert s1 == s2


def test_sample_stability_under_out_of_range_append(ctx) -> None:
    _load_range(ctx, range(1, 10_001))
    from nu.virtuals.interactions.kh57 import Kh57SampleQuery

    # Fresh seeded rng per run so the rng state does not drift.
    q1 = Kh57SampleQuery(Ledger.entries, 50, 1_000, 2_000, rng=random.Random(0))
    s1 = run(q1, ctx)[0]
    # Append keys outside the queried range [1000, 2000).
    for k in range(10_001, 20_001):
        run(Ledger.entries.set(k, k * 2), ctx)
    q2 = Kh57SampleQuery(Ledger.entries, 50, 1_000, 2_000, rng=random.Random(0))
    s2 = run(q2, ctx)[0]
    assert set(s1) == set(s2)


# ============================================================================
# RANGE
# ============================================================================


def test_range_yields_in_key_order(ctx) -> None:
    _load_range(ctx, [500, 100, 300, 200, 400])
    got = list(run(Ledger.entries.range(150, 450), ctx)[0])
    assert [k for k, _ in got] == [200, 300, 400]
    assert [v for _, v in got] == [400, 600, 800]


def test_range_empty(ctx) -> None:
    got = list(run(Ledger.entries.range(0, 10), ctx)[0])
    assert got == []


# ============================================================================
# FACET
# ============================================================================


def test_facet_switch_returns_clone(ctx) -> None:
    ref = Ledger.entries
    eager = ref.eager
    lazy = ref.lazy
    assert eager._facet is Facet.EAGER
    assert lazy._facet is Facet.LAZY
    # switching preserves the shape / address
    assert eager._segment == ref._segment
