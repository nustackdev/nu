"""Unit tests for ``nu.lang.runtime.context.context``.

Covers ``Context`` -- a stack of immutable fabric frames. ``bind`` / ``lazy``
push a frame and return a new Context, resolution by type then scope tags with
subset fallback, per-key shadowing across frames, predicate-guarded reads,
lazy entries built once, and the temporary attrs table.
"""

from __future__ import annotations

import pytest

from nu.lang.runtime import Attributes, Context


# --- service tags (test-only) ---------------------------------------------


class Storage:
    """Marker service type."""


class View:
    """Marker service type."""


class Market:
    """Marker scope tag."""


class OrderShape:
    """Marker scope tag."""


class Shard:
    """Marker scope tag."""


# --- attrs property -------------------------------------------------------


def test_fresh_context_exposes_empty_stores() -> None:
    ctx = Context()
    assert isinstance(ctx.attrs, Attributes)
    assert dict(ctx.attrs.items()) == {}
    assert ctx.has(Storage) is False


def test_context_seeds_its_starting_names() -> None:
    seed = {"x": 1}
    ctx = Context(attrs=seed)
    assert ctx.attrs.get("x") == 1
    ctx.attrs.set("x", 2)
    assert seed == {"x": 1}  # the seed is copied in, not adopted


# --- bind: eager basic ----------------------------------------------------


def test_bind_returns_new_context_without_mutating_original() -> None:
    ctx0 = Context()
    ctx1 = ctx0.bind(Storage, "rocks")
    assert ctx1 is not ctx0
    assert ctx1.get(Storage) == "rocks"
    assert not ctx0.has(Storage)


def test_bind_by_type_resolves_eagerly() -> None:
    ctx = Context().bind(Storage, "value")
    assert ctx.get(Storage) == "value"


def test_bind_with_scope_tag_separates_bindings() -> None:
    ctx = Context().bind(Storage, "default").bind(Storage, "orders", OrderShape)
    assert ctx.get(Storage) == "default"
    assert ctx.get(Storage, OrderShape) == "orders"


def test_bind_overwrite_at_same_scope() -> None:
    ctx = Context().bind(Storage, "a").bind(Storage, "b")
    assert ctx.get(Storage) == "b"


# --- has ------------------------------------------------------------------


def test_has_true_when_bound() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.has(Storage) is True


def test_has_false_when_unbound() -> None:
    assert Context().has(Storage) is False


def test_has_falls_back_to_empty_scope() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.has(Storage, Market) is True


# --- get: failure ---------------------------------------------------------


def test_get_raises_lookup_error_when_unbound() -> None:
    with pytest.raises(LookupError, match="No binding"):
        Context().get(Storage)


def test_get_error_mentions_type_name() -> None:
    with pytest.raises(LookupError, match="Storage"):
        Context().get(Storage)


def test_get_error_mentions_scope_tags() -> None:
    with pytest.raises(LookupError, match="Market"):
        Context().get(View, Market)


# --- resolution: scope-tag subset fallback --------------------------------


def test_subset_fallback_matches_smaller_scope() -> None:
    ctx = Context().bind(Storage, "default")
    assert ctx.get(Storage, Market) == "default"


def test_subset_fallback_prefers_more_specific() -> None:
    ctx = Context().bind(Storage, "default").bind(Storage, "for-market", Market)
    assert ctx.get(Storage, Market) == "for-market"
    assert ctx.get(Storage, Market, Shard) == "for-market"


def test_subset_fallback_picks_partial_match() -> None:
    ctx = Context().bind(Storage, "AB", Market, Shard)
    assert ctx.get(Storage, Market, Shard) == "AB"


# --- lazy bindings --------------------------------------------------------


def test_lazy_is_not_resolved_until_get() -> None:
    calls: list[int] = []

    def factory() -> str:
        calls.append(1)
        return "made"

    ctx = Context().lazy(Storage, factory)
    assert ctx.was_opened(Storage) is False
    assert calls == []
    assert ctx.get(Storage) == "made"
    assert ctx.was_opened(Storage) is True
    assert calls == [1]


def test_lazy_factory_runs_once_and_caches() -> None:
    calls: list[int] = []

    def factory() -> int:
        calls.append(1)
        return 42

    ctx = Context().lazy(Storage, factory)
    assert ctx.get(Storage) == 42
    assert ctx.get(Storage) == 42
    assert calls == [1]


def test_was_opened_false_for_eager_binding() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.was_opened(Storage) is False


# --- predicate-guarded bindings -------------------------------------------


def test_predicate_match_selects_value() -> None:
    ctx = Context().bind(
        View,
        "shard_a",
        Market,
        sharding=lambda site, **_: site[0] < 16,
    )
    assert ctx.get(View, Market, site=(5,)) == "shard_a"


def test_predicate_mismatch_raises_lookup() -> None:
    ctx = Context().bind(
        View,
        "shard_a",
        Market,
        sharding=lambda site, **_: site[0] < 16,
    )
    with pytest.raises(LookupError):
        ctx.get(View, Market, site=(20,))


def test_predicate_multiple_entries_or_across() -> None:
    ctx = (
        Context()
        .bind(View, "low", Market, sharding=lambda site, **_: site[0] < 16)
        .bind(View, "high", Market, sharding=lambda site, **_: site[0] >= 16)
    )
    assert ctx.get(View, Market, site=(5,)) == "low"
    assert ctx.get(View, Market, site=(20,)) == "high"


def test_predicate_all_must_pass_and() -> None:
    ctx = Context().bind(
        View,
        "value",
        Market,
        a=lambda x, **_: x > 0,
        b=lambda x, **_: x < 10,
    )
    assert ctx.get(View, Market, x=5) == "value"
    with pytest.raises(LookupError):
        ctx.get(View, Market, x=-1)
    with pytest.raises(LookupError):
        ctx.get(View, Market, x=20)


# --- predicates -------------------------------------------------------


def test_predicates_returns_all_entries_at_scope() -> None:
    p1 = lambda **_: True  # noqa: E731
    p2 = lambda **_: False  # noqa: E731
    ctx = Context().bind(View, "a", Market, gate=p1).bind(View, "b", Market, gate=p2)
    entries = ctx.predicates(View, Market)
    assert len(entries) == 2
    values = [v for _, v in entries]
    assert "a" in values
    assert "b" in values


def test_predicates_filters_by_scope() -> None:
    ctx = (
        Context()
        .bind(View, "a", Market, gate=lambda **_: True)
        .bind(View, "b", Shard, gate=lambda **_: True)
    )
    market_entries = ctx.predicates(View, Market)
    assert len(market_entries) == 1
    assert market_entries[0][1] == "a"


def test_predicates_returns_empty_when_none() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.predicates(Storage) == []


# --- immutability ---------------------------------------------------------


def test_bind_chain_does_not_mutate_earlier_contexts() -> None:
    ctx0 = Context()
    ctx1 = ctx0.bind(Storage, "a")
    ctx2 = ctx1.bind(View, "b")
    assert ctx0.has(Storage) is False
    assert ctx1.has(View) is False
    assert ctx2.has(Storage) is True
    assert ctx2.has(View) is True


def test_bind_shares_the_attrs_table_of_its_task() -> None:
    # attrs are one task's table until they go (task-184 phase 4): a frame
    # pushed inside the task sees and sets the same names.
    ctx0 = Context(attrs={"k": 1})
    ctx1 = ctx0.bind(Storage, "v")
    ctx1.attrs.set("k", 2)
    assert ctx0.attrs.get("k") == 2


# --- frames -----------------------------------------------------------------


def test_an_inner_frame_shadows_the_same_key() -> None:
    outer = Context().bind(Storage, "outer")
    inner = outer.bind(Storage, "inner")
    assert inner.get(Storage) == "inner"
    assert outer.get(Storage) == "outer"


def test_nesting_never_reroutes_a_tagged_lookup() -> None:
    # Shadowing is per key: an inner untagged binding does not hide an outer
    # tagged one from a tagged lookup.
    ctx = Context().bind(Storage, "orders", OrderShape).bind(Storage, "plain")
    assert ctx.get(Storage, OrderShape) == "orders"
    assert ctx.get(Storage) == "plain"
    assert ctx.get(Storage, Market) == "plain"


def test_an_inner_frame_shadows_a_tagged_key_only_for_that_key() -> None:
    ctx = (
        Context()
        .bind(Storage, "plain")
        .bind(Storage, "outer-orders", OrderShape)
        .bind(Storage, "inner-orders", OrderShape)
    )
    assert ctx.get(Storage, OrderShape) == "inner-orders"
    assert ctx.get(Storage) == "plain"


def test_an_inner_guarded_binding_shadows_the_same_predicates() -> None:
    gate = lambda site, **_: site < 16  # noqa: E731
    ctx = Context().bind(View, "outer", Market, gate=gate).bind(View, "inner", Market, gate=gate)
    assert ctx.get(View, Market, site=5) == "inner"
    assert [v for _, v in ctx.predicates(View, Market)] == ["inner"]


def test_guarded_bindings_list_outermost_first() -> None:
    ctx = (
        Context()
        .bind(View, "a", Market, gate=lambda **_: True)
        .bind(View, "b", Market, gate=lambda **_: True)
    )
    assert [v for _, v in ctx.predicates(View, Market)] == ["a", "b"]


def test_a_lazy_binding_is_shared_by_every_context_above_its_frame() -> None:
    calls: list[int] = []
    ctx = Context().lazy(Storage, lambda: calls.append(1) or "made")
    one, two = ctx.bind(View, "w"), ctx.bind(View, "x")
    assert one.get(Storage) == "made"
    assert two.get(Storage) == "made"
    assert ctx.get(Storage) == "made"
    assert calls == [1]


def test_a_lazy_binding_builds_once_under_concurrent_first_lookups() -> None:
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    calls: list[int] = []
    start = threading.Barrier(8)

    def factory() -> object:
        calls.append(1)
        time.sleep(0.02)  # wide window: every thread is in the lookup now
        return object()

    ctx = Context().lazy(Storage, factory)

    def look() -> object:
        start.wait()
        return ctx.get(Storage)

    with ThreadPoolExecutor(8) as pool:
        got = list(pool.map(lambda _: look(), range(8)))
    assert calls == [1]
    assert all(g is got[0] for g in got)


def test_was_opened_reads_the_nearest_binding_of_the_key() -> None:
    ctx = Context().lazy(Storage, lambda: "lazy")
    ctx.get(Storage)
    inner = ctx.bind(Storage, "eager")
    assert ctx.was_opened(Storage) is True
    assert inner.was_opened(Storage) is False


def test_attrs_fork_shares_the_frames_and_copies_the_table() -> None:
    ctx = Context(attrs={"item": 1}).bind(Storage, "v")
    arm = ctx._fork_attrs()
    arm.attrs.set("item", 2)
    assert ctx.attrs.get("item") == 1
    assert arm.get(Storage) == "v"


# --- repr -----------------------------------------------------------------


def test_repr_includes_bindings() -> None:
    ctx = Context().bind(Storage, "v").bind(View, "w", Market)
    r = repr(ctx)
    assert "Storage" in r
    assert "View" in r
    assert "Market" in r


def test_repr_marks_lazy_bindings() -> None:
    ctx = Context().lazy(Storage, lambda: 1)
    assert "lazy" in repr(ctx)
