"""Unit tests for ``nu.lang.runtime.context.context``.

Covers ``Context`` -- one task's environment, an attrs store and a fabrics
store. Seeding with ``Context(attrs=...)``, the setup-time ``bind`` / ``lazy``
that return a new Context, resolution by type then scope tags with subset
fallback, predicate-guarded reads, and ``branch`` for a starting task. The
scoped ``fabrics.bind`` / ``lazy`` live in ``test_fabrics.py``.
"""

from __future__ import annotations

import pytest

from nu.lang.runtime import Attributes, Context, Fabrics


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
    assert isinstance(ctx.fabrics, Fabrics)
    assert dict(ctx.attrs.items()) == {}
    assert ctx.fabrics.has(Storage) is False


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
    assert ctx1.fabrics.get(Storage) == "rocks"
    assert not ctx0.fabrics.has(Storage)


def test_bind_by_type_resolves_eagerly() -> None:
    ctx = Context().bind(Storage, "value")
    assert ctx.fabrics.get(Storage) == "value"


def test_bind_with_scope_tag_separates_bindings() -> None:
    ctx = Context().bind(Storage, "default").bind(Storage, "orders", OrderShape)
    assert ctx.fabrics.get(Storage) == "default"
    assert ctx.fabrics.get(Storage, OrderShape) == "orders"


def test_bind_overwrite_at_same_scope() -> None:
    ctx = Context().bind(Storage, "a").bind(Storage, "b")
    assert ctx.fabrics.get(Storage) == "b"


# --- has ------------------------------------------------------------------


def test_has_true_when_bound() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.fabrics.has(Storage) is True


def test_has_false_when_unbound() -> None:
    assert Context().fabrics.has(Storage) is False


def test_has_falls_back_to_empty_scope() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.fabrics.has(Storage, Market) is True


# --- get: failure ---------------------------------------------------------


def test_get_raises_lookup_error_when_unbound() -> None:
    with pytest.raises(LookupError, match="No binding"):
        Context().fabrics.get(Storage)


def test_get_error_mentions_type_name() -> None:
    with pytest.raises(LookupError, match="Storage"):
        Context().fabrics.get(Storage)


def test_get_error_mentions_scope_tags() -> None:
    with pytest.raises(LookupError, match="Market"):
        Context().fabrics.get(View, Market)


# --- resolution: scope-tag subset fallback --------------------------------


def test_subset_fallback_matches_smaller_scope() -> None:
    ctx = Context().bind(Storage, "default")
    assert ctx.fabrics.get(Storage, Market) == "default"


def test_subset_fallback_prefers_more_specific() -> None:
    ctx = Context().bind(Storage, "default").bind(Storage, "for-market", Market)
    assert ctx.fabrics.get(Storage, Market) == "for-market"
    assert ctx.fabrics.get(Storage, Market, Shard) == "for-market"


def test_subset_fallback_picks_partial_match() -> None:
    ctx = Context().bind(Storage, "AB", Market, Shard)
    assert ctx.fabrics.get(Storage, Market, Shard) == "AB"


# --- lazy bindings --------------------------------------------------------


def test_lazy_is_not_resolved_until_get() -> None:
    calls: list[int] = []

    def factory() -> str:
        calls.append(1)
        return "made"

    ctx = Context().lazy(Storage, factory)
    assert ctx.fabrics.was_opened(Storage) is False
    assert calls == []
    assert ctx.fabrics.get(Storage) == "made"
    assert ctx.fabrics.was_opened(Storage) is True
    assert calls == [1]


def test_lazy_factory_runs_once_and_caches() -> None:
    calls: list[int] = []

    def factory() -> int:
        calls.append(1)
        return 42

    ctx = Context().lazy(Storage, factory)
    assert ctx.fabrics.get(Storage) == 42
    assert ctx.fabrics.get(Storage) == 42
    assert calls == [1]


def test_was_opened_false_for_eager_binding() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.fabrics.was_opened(Storage) is False


# --- predicate-guarded bindings -------------------------------------------


def test_predicate_match_selects_value() -> None:
    ctx = Context().bind(
        View,
        "shard_a",
        Market,
        sharding=lambda site, **_: site[0] < 16,
    )
    assert ctx.fabrics.get(View, Market, site=(5,)) == "shard_a"


def test_predicate_mismatch_raises_lookup() -> None:
    ctx = Context().bind(
        View,
        "shard_a",
        Market,
        sharding=lambda site, **_: site[0] < 16,
    )
    with pytest.raises(LookupError):
        ctx.fabrics.get(View, Market, site=(20,))


def test_predicate_multiple_entries_or_across() -> None:
    ctx = (
        Context()
        .bind(View, "low", Market, sharding=lambda site, **_: site[0] < 16)
        .bind(View, "high", Market, sharding=lambda site, **_: site[0] >= 16)
    )
    assert ctx.fabrics.get(View, Market, site=(5,)) == "low"
    assert ctx.fabrics.get(View, Market, site=(20,)) == "high"


def test_predicate_all_must_pass_and() -> None:
    ctx = Context().bind(
        View,
        "value",
        Market,
        a=lambda x, **_: x > 0,
        b=lambda x, **_: x < 10,
    )
    assert ctx.fabrics.get(View, Market, x=5) == "value"
    with pytest.raises(LookupError):
        ctx.fabrics.get(View, Market, x=-1)
    with pytest.raises(LookupError):
        ctx.fabrics.get(View, Market, x=20)


# --- predicates -------------------------------------------------------


def test_predicates_returns_all_entries_at_scope() -> None:
    p1 = lambda **_: True  # noqa: E731
    p2 = lambda **_: False  # noqa: E731
    ctx = Context().bind(View, "a", Market, gate=p1).bind(View, "b", Market, gate=p2)
    entries = ctx.fabrics.predicates(View, Market)
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
    market_entries = ctx.fabrics.predicates(View, Market)
    assert len(market_entries) == 1
    assert market_entries[0][1] == "a"


def test_predicates_returns_empty_when_none() -> None:
    ctx = Context().bind(Storage, "v")
    assert ctx.fabrics.predicates(Storage) == []


# --- immutability ---------------------------------------------------------


def test_bind_chain_does_not_mutate_earlier_contexts() -> None:
    ctx0 = Context()
    ctx1 = ctx0.bind(Storage, "a")
    ctx2 = ctx1.bind(View, "b")
    assert ctx0.fabrics.has(Storage) is False
    assert ctx1.fabrics.has(View) is False
    assert ctx2.fabrics.has(Storage) is True
    assert ctx2.fabrics.has(View) is True


def test_bind_carries_the_names_as_a_branch() -> None:
    ctx0 = Context(attrs={"k": 1})
    ctx1 = ctx0.bind(Storage, "v")
    assert ctx1.attrs.get("k") == 1
    ctx1.attrs.set("k", 2)
    assert ctx0.attrs.get("k") == 1


# --- branch ---------------------------------------------------------------


def test_branch_gives_its_own_attrs_table() -> None:
    ctx = Context(attrs={"item": 1})
    arm = ctx.branch()
    arm.attrs.set("item", 2)
    with arm.attrs.let("mine", True):
        assert not ctx.attrs.exists("mine")
    assert ctx.attrs.get("item") == 1


def test_branch_shares_attr_values_by_reference() -> None:
    ctx = Context(attrs={"k": [1, 2]})
    arm = ctx.branch()
    arm.attrs.get("k").append(3)  # type: ignore[attr-defined]
    assert ctx.attrs.get("k") is arm.attrs.get("k")
    assert ctx.attrs.get("k") == [1, 2, 3]


def test_branch_keeps_the_bindings() -> None:
    ctx = Context().bind(Storage, "v").bind(View, "w", Market)
    arm = ctx.branch()
    assert arm.fabrics.get(Storage) == "v"
    assert arm.fabrics.get(View, Market) == "w"


def test_branch_gives_its_own_fabrics_table() -> None:
    ctx = Context()
    arm = ctx.branch()
    with arm.fabrics.bind(Storage, "v"):
        assert arm.fabrics.has(Storage) is True
        assert ctx.fabrics.has(Storage) is False


def test_branch_shares_a_lazy_instance() -> None:
    calls: list[int] = []
    ctx = Context().lazy(Storage, lambda: calls.append(1) or "made")
    arm = ctx.branch()
    assert arm.fabrics.get(Storage) == "made"
    assert ctx.fabrics.get(Storage) == "made"
    assert calls == [1]


def test_branch_binding_does_not_leak_back() -> None:
    ctx = Context()
    arm = ctx.branch().bind(Storage, "v")
    assert ctx.fabrics.has(Storage) is False
    assert arm.fabrics.has(Storage) is True


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
