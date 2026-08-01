"""Tests for nu-virtuals collection refs — DictRef, ListRef, SetRef, ShapeRef.

Verifies:
- Correct Value types from _wrap_* methods
- Lazy/eager facet switching
- Collection operations execute correctly through virtuals views
- Proper KeysView/ValuesView/ItemsView from virtuals
- Faceted execution produces correct results
"""

from __future__ import annotations

import builtins
from collections.abc import ItemsView, KeysView, ValuesView

import pytest

from nu import (
    ContainsQuery,
    Context,
    DictForm,
    DictItemsForm,
    DictKeysForm,
    DictValuesForm,
    IteratorForm,
    LenQuery,
    ListForm,
    LiteralQuery,
    SetForm,
    SortedQuery,
    arun,
    run,
)
from nu.domains.shape import Shape
from nu.virtuals import (
    DictRef,
    FloatRef,
    IntRef,
    Kh57Ref,
    Kh57ShapesRef,
    ListRef,
    SetRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
)
from nu.virtuals.refs.base import Facet
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol


# ============================================================================
# SHAPES
# ============================================================================


class Order(Shape):
    symbol = StrRef.slot()
    price = FloatRef.slot()
    qty = IntRef.slot()


class Portfolio(Shape):
    name = StrRef.slot()
    tags = ListRef.slot(str)
    metadata = DictRef.slot(str)
    members = SetRef.slot(str)
    orders = ShapesListRef.slot(Order)
    team = ShapesDictRef.slot(Order)
    events = Kh57Ref.slot(str)
    series = Kh57ShapesRef.slot(Order)


# ============================================================================
# HELPERS
# ============================================================================


@pytest.fixture
def portfolio_ctx(nav, tx):
    """Context with Portfolio shape bindings (v2 type-first bind)."""
    return (
        Context()
        .bind(Navigator, nav)
        .bind(Navigator, nav, Portfolio)
        .bind(TransactionProtocol, tx)
        .bind(TransactionProtocol, tx, Portfolio)
    )


def set(ref, value, ctx):
    run(ref.set(value), ctx)


# ============================================================================
# FACET TESTS — lazy/eager switching
# ============================================================================


class TestFacets:
    """Facet switching on ViewRef."""

    def test_default_facet_is_lazy(self):
        assert Portfolio.metadata._payload.get("facet", Facet.LAZY) is Facet.LAZY

    def test_eager_property(self):
        eager = Portfolio.metadata.eager
        assert eager._payload.get("facet", Facet.LAZY) is Facet.EAGER

    def test_lazy_property_noop(self):
        ref = Portfolio.metadata
        lazy = ref.lazy
        assert lazy is ref

    def test_eager_lazy_roundtrip(self):
        ref = Portfolio.metadata.eager.lazy
        assert ref._payload.get("facet", Facet.LAZY) is Facet.LAZY

    def test_lazy_eager_roundtrip(self):
        ref = Portfolio.metadata.lazy.eager
        assert ref._payload.get("facet", Facet.LAZY) is Facet.EAGER

    def test_eager_is_copy_not_same(self):
        ref = Portfolio.metadata
        eager = ref.eager
        assert eager is not ref
        assert eager._payload.get("facet", Facet.LAZY) is Facet.EAGER
        assert ref._payload.get("facet", Facet.LAZY) is Facet.LAZY

    def test_eager_eager_is_noop(self):
        eager1 = Portfolio.metadata.eager
        eager2 = eager1.eager
        assert eager2 is eager1

    def test_facet_on_list_ref(self):
        assert Portfolio.tags._payload.get("facet", Facet.LAZY) is Facet.LAZY
        assert Portfolio.tags.eager._payload.get("facet", Facet.LAZY) is Facet.EAGER

    def test_facet_on_set_ref(self):
        assert Portfolio.members._payload.get("facet", Facet.LAZY) is Facet.LAZY
        assert Portfolio.members.eager._payload.get("facet", Facet.LAZY) is Facet.EAGER


# ============================================================================
# DICT REF — wrapping types
# ============================================================================


class TestDictRefWrapTypes:
    """DictRef returns DictKeysForm/DictValuesForm/DictItemsForm."""

    def test_keys_returns_dict_keys_value(self):
        keys = Portfolio.metadata.keys()
        assert isinstance(keys, DictKeysForm)

    def test_values_returns_dict_values_value(self):
        vals = Portfolio.metadata.values()
        assert isinstance(vals, DictValuesForm)

    def test_items_returns_dict_items_value(self):
        items = Portfolio.metadata.items()
        assert isinstance(items, DictItemsForm)

    def test_result_returns_dict_value(self):
        result = Portfolio.metadata._wrap_result(LiteralQuery("x"))
        assert isinstance(result, DictForm)


class TestDictRefExecution:
    """DictRef operations produce correct results through virtuals."""

    @pytest.mark.asyncio
    async def test_set_and_keys(self, portfolio_ctx):
        # kept async: representative round-trip test for the async path
        set(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = (await arun(Portfolio.metadata.keys(), portfolio_ctx))[0]
        assert isinstance(result, KeysView)
        assert builtins.set(result) == {"strategy", "risk"}

    def test_set_and_values(self, portfolio_ctx):
        set(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = run(Portfolio.metadata.values(), portfolio_ctx)[0]
        assert isinstance(result, ValuesView)
        assert builtins.set(result) == {"momentum", "medium"}

    def test_set_and_items(self, portfolio_ctx):
        set(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = run(Portfolio.metadata.items(), portfolio_ctx)[0]
        assert isinstance(result, ItemsView)
        assert builtins.set(result) == {("strategy", "momentum"), ("risk", "medium")}

    def test_get(self, portfolio_ctx):
        set(Portfolio.metadata, {"key": "value"}, portfolio_ctx)
        result = run(Portfolio.metadata.get_item("key"), portfolio_ctx)[0]
        assert result == "value"

    def test_set_item(self, portfolio_ctx):
        set(Portfolio.metadata, {}, portfolio_ctx)
        run(Portfolio.metadata.set_item("new_key", "new_val"), portfolio_ctx)
        result = run(Portfolio.metadata.get_item("new_key"), portfolio_ctx)[0]
        assert result == "new_val"


# ============================================================================
# LIST REF — iteration and slicing
# ============================================================================


class TestListRefWrapTypes:
    """ListRef wrapping types."""

    def test_iterable_is_iterator_value(self):
        wrapped = Portfolio.tags._wrap_iterable_result(LiteralQuery("x"))
        assert isinstance(wrapped, IteratorForm)

    def test_sliceable_is_list_value(self):
        wrapped = Portfolio.tags._wrap_sliceable_result(LiteralQuery("x"))
        assert isinstance(wrapped, ListForm)


class TestListRefExecution:
    """ListRef operations through virtuals."""

    @pytest.mark.asyncio
    async def test_set_and_first(self, portfolio_ctx):
        # kept async: representative round-trip test for the async path
        set(Portfolio.tags, ["alpha", "beta", "gamma"], portfolio_ctx)
        result = (await arun(Portfolio.tags.first_elem(), portfolio_ctx))[0]
        assert result == "alpha"

    def test_set_and_last(self, portfolio_ctx):
        set(Portfolio.tags, ["alpha", "beta", "gamma"], portfolio_ctx)
        result = run(Portfolio.tags.last_elem(), portfolio_ctx)[0]
        assert result == "gamma"

    def test_set_and_slice(self, portfolio_ctx):
        set(Portfolio.tags, ["a", "b", "c", "d", "e"], portfolio_ctx)
        result = run(Portfolio.tags.slice(1, 3), portfolio_ctx)[0]
        assert list(result) == ["b", "c"]

    def test_append(self, portfolio_ctx):
        set(Portfolio.tags, ["x"], portfolio_ctx)
        run(Portfolio.tags.append("y"), portfolio_ctx)
        result = run(Portfolio.tags, portfolio_ctx)[0]
        assert list(result) == ["x", "y"]


# ============================================================================
# SET REF
# ============================================================================


class TestSetRefWrapTypes:
    """SetRef wrapping types."""

    def test_set_result_is_set_value(self):
        wrapped = Portfolio.members._wrap_set_result(LiteralQuery("x"))
        assert isinstance(wrapped, SetForm)


class TestSetRefExecution:
    """SetRef operations through virtuals."""

    def test_set_and_add(self, portfolio_ctx):
        set(Portfolio.members, {"alice"}, portfolio_ctx)
        run(Portfolio.members.add("bob"), portfolio_ctx)
        result = run(Portfolio.members, portfolio_ctx)[0]
        assert builtins.set(result) == {"alice", "bob"}

    def test_union(self, portfolio_ctx):
        set(Portfolio.members, {"alice", "bob"}, portfolio_ctx)
        result = run(Portfolio.members.union({"bob", "charlie"}), portfolio_ctx)[0]
        assert result == {"alice", "bob", "charlie"}


# ============================================================================
# SHAPES LIST REF — sequence of shapes
# ============================================================================


class TestShapesListRefExecution:
    """ShapesListRef operations through virtuals."""

    def test_set_and_navigate(self, portfolio_ctx):
        set(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
            ],
            portfolio_ctx,
        )
        result = run(Portfolio.orders[0].symbol, portfolio_ctx)[0]
        assert result == "AAPL"

    def test_set_and_second_element(self, portfolio_ctx):
        set(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
            ],
            portfolio_ctx,
        )
        result = run(Portfolio.orders[1].price, portfolio_ctx)[0]
        assert result == 142.3


# ============================================================================
# SHAPES DICT REF — mapping of shapes
# ============================================================================


class TestShapesDictRefWrapTypes:
    """ShapesDictRef returns DictKeysForm/DictValuesForm/DictItemsForm."""

    def test_keys_returns_dict_keys_value(self):
        keys = Portfolio.team.keys()
        assert isinstance(keys, DictKeysForm)

    def test_values_returns_dict_values_value(self):
        vals = Portfolio.team.values()
        assert isinstance(vals, DictValuesForm)

    def test_items_returns_dict_items_value(self):
        items = Portfolio.team.items()
        assert isinstance(items, DictItemsForm)


class TestShapesDictRefExecution:
    """ShapesDictRef operations through virtuals."""

    def test_set_and_keys(self, portfolio_ctx):
        set(
            Portfolio.team,
            {
                "desk_a": {"symbol": "AAPL", "price": 185.5, "qty": 10},
                "desk_b": {"symbol": "GOOG", "price": 142.3, "qty": 5},
            },
            portfolio_ctx,
        )
        result = run(Portfolio.team.keys(), portfolio_ctx)[0]
        assert builtins.set(result) == {"desk_a", "desk_b"}

    def test_slot_navigation(self, portfolio_ctx):
        set(
            Portfolio.team,
            {
                "desk_a": {"symbol": "AAPL", "price": 185.5, "qty": 10},
            },
            portfolio_ctx,
        )
        result = run(Portfolio.team["desk_a"].symbol, portfolio_ctx)[0]
        assert result == "AAPL"


# ============================================================================
# KH57 REF — sparse int-keyed map with range sampling
# ============================================================================


class TestKh57RefWrapTypes:
    """Kh57Ref inherits DictRef wrapping — DictKeysForm/DictValuesForm/DictItemsForm."""

    def test_keys_returns_dict_keys_value(self):
        keys = Portfolio.events.keys()
        assert isinstance(keys, DictKeysForm)

    def test_values_returns_dict_values_value(self):
        vals = Portfolio.events.values()
        assert isinstance(vals, DictValuesForm)

    def test_items_returns_dict_items_value(self):
        items = Portfolio.events.items()
        assert isinstance(items, DictItemsForm)

    def test_result_returns_dict_value(self):
        result = Portfolio.events._wrap_result(LiteralQuery("x"))
        assert isinstance(result, DictForm)


class TestKh57RefExecution:
    """Kh57Ref operations through virtuals."""

    def test_set_and_get(self, portfolio_ctx):
        run(Portfolio.events.set_item(42, "open"), portfolio_ctx)
        assert run(Portfolio.events.get_item(42), portfolio_ctx)[0] == "open"

    def test_set_and_keys(self, portfolio_ctx):
        set(Portfolio.events, {1: "a", 5: "b", 999: "c"}, portfolio_ctx)
        result = run(Portfolio.events.keys(), portfolio_ctx)[0]
        assert isinstance(result, KeysView)
        assert builtins.set(result) == {1, 5, 999}

    def test_set_and_values(self, portfolio_ctx):
        set(Portfolio.events, {1: "a", 5: "b"}, portfolio_ctx)
        result = run(Portfolio.events.values(), portfolio_ctx)[0]
        assert builtins.set(result) == {"a", "b"}

    def test_range_slice(self, portfolio_ctx):
        set(Portfolio.events, {i: str(i) for i in range(20)}, portfolio_ctx)
        result = run(Portfolio.events.range(5, 10), portfolio_ctx)[0]
        assert result == [(i, str(i)) for i in range(5, 10)]

    def test_sample_yields_up_to_n(self, portfolio_ctx):
        set(Portfolio.events, {i: str(i) for i in range(100)}, portfolio_ctx)
        result = run(Portfolio.events.sample(10), portfolio_ctx)[0]
        assert len(result) == 10
        for k, v in result:
            assert 0 <= k < 100
            assert v == str(k)


# ============================================================================
# KH57 SHAPES REF — mapping of shapes with range sampling
# ============================================================================


class TestKh57ShapesRefWrapTypes:
    """Kh57ShapesRef inherits ShapesDictRef wrapping."""

    def test_keys_returns_dict_keys_value(self):
        keys = Portfolio.series.keys()
        assert isinstance(keys, DictKeysForm)

    def test_values_returns_dict_values_value(self):
        vals = Portfolio.series.values()
        assert isinstance(vals, DictValuesForm)

    def test_items_returns_dict_items_value(self):
        items = Portfolio.series.items()
        assert isinstance(items, DictItemsForm)


class TestKh57ShapesRefExecution:
    """Kh57ShapesRef operations through virtuals."""

    def test_set_and_keys(self, portfolio_ctx):
        set(
            Portfolio.series,
            {
                100: {"symbol": "AAPL", "price": 185.5, "qty": 10},
                200: {"symbol": "GOOG", "price": 142.3, "qty": 5},
            },
            portfolio_ctx,
        )
        result = run(Portfolio.series.keys(), portfolio_ctx)[0]
        assert builtins.set(result) == {100, 200}

    def test_slot_navigation(self, portfolio_ctx):
        set(
            Portfolio.series,
            {100: {"symbol": "AAPL", "price": 185.5, "qty": 10}},
            portfolio_ctx,
        )
        assert run(Portfolio.series[100].symbol, portfolio_ctx)[0] == "AAPL"
        assert run(Portfolio.series[100].price, portfolio_ctx)[0] == 185.5


# ============================================================================
# TERM COMPOSITION
# ============================================================================


class TestTermComposition:
    """Nu arithmetic across refs."""

    def test_multiply(self, portfolio_ctx):
        set(
            Portfolio.orders,
            [{"symbol": "AAPL", "price": 185.5, "qty": 10}],
            portfolio_ctx,
        )
        total = Portfolio.orders[0].price * Portfolio.orders[0].qty
        result = run(total, portfolio_ctx)[0]
        assert result == 1855.0

    def test_subtract(self, portfolio_ctx):
        set(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
            ],
            portfolio_ctx,
        )
        spread = Portfolio.orders[0].price - Portfolio.orders[1].price
        result = run(spread, portfolio_ctx)[0]
        assert abs(result - 43.2) < 0.01


# ============================================================================
# LAZY TAKE — islice over keys/values/items (deferred until TakeQuery lands)
# ============================================================================


@pytest.mark.skip(reason="TakeQuery not yet ported to v2")
class TestLazyTake:
    """Take(keys, n) lazily slices collections via itertools.islice."""

    def test_take_keys(self, portfolio_ctx):
        set(Portfolio.metadata, {f"k{i}": f"v{i}" for i in range(50)}, portfolio_ctx)
        result = run(Take(Portfolio.metadata.keys(), 5).to_list(), portfolio_ctx)[0]  # noqa: F821
        assert len(result) == 5

    def test_take_values(self, portfolio_ctx):
        set(Portfolio.metadata, {f"k{i}": f"v{i}" for i in range(50)}, portfolio_ctx)
        result = run(Take(Portfolio.metadata.values(), 3).to_list(), portfolio_ctx)[0]  # noqa: F821
        assert len(result) == 3

    def test_take_items(self, portfolio_ctx):
        set(Portfolio.metadata, {"a": "1", "b": "2", "c": "3"}, portfolio_ctx)
        result = run(Take(Portfolio.metadata.items(), 2).to_list(), portfolio_ctx)[0]  # noqa: F821
        assert len(result) == 2

    def test_take_list(self, portfolio_ctx):
        set(Portfolio.tags, ["a", "b", "c", "d", "e"], portfolio_ctx)
        result = run(Take(Portfolio.tags, 3).to_list(), portfolio_ctx)[0]  # noqa: F821
        assert result == ["a", "b", "c"]

    def test_take_more_than_available(self, portfolio_ctx):
        set(Portfolio.metadata, {"a": "1", "b": "2"}, portfolio_ctx)
        result = run(Take(Portfolio.metadata.keys(), 100).to_list(), portfolio_ctx)[0]  # noqa: F821
        assert sorted(result) == ["a", "b"]

    def test_take_returns_iterator_value(self):
        term = Take(Portfolio.metadata.keys(), 10)  # noqa: F821
        assert isinstance(term, IteratorForm)


# ============================================================================
# END-TO-END — full scenario through virtuals
# ============================================================================


class TestEndToEnd:
    """Full scenario: populate, navigate, query, mutate, compose."""

    @pytest.mark.asyncio
    async def test_full_scenario(self, portfolio_ctx):
        ctx = portfolio_ctx

        # --- populate ---
        set(Portfolio.name, "Main Portfolio", ctx)
        set(Portfolio.tags, ["alpha", "beta", "gamma", "delta", "epsilon"], ctx)
        set(Portfolio.metadata, {"strategy": "momentum", "risk": "medium", "horizon": "long"}, ctx)
        set(Portfolio.members, {"alice", "bob", "charlie"}, ctx)
        set(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
                {"symbol": "TSLA", "price": 245.0, "qty": 3},
            ],
            ctx,
        )

        # --- primitives ---
        assert (await arun(Portfolio.name, ctx))[0] == "Main Portfolio"

        # --- dict keys iteration ---
        keys = (await arun(Portfolio.metadata.keys(), ctx))[0]
        assert builtins.set(keys) == {"strategy", "risk", "horizon"}

        # --- dict get ---
        assert (await arun(Portfolio.metadata.get_item("strategy"), ctx))[0] == "momentum"

        # (lazy Take over keys covered in TestLazyTake — skipped until TakeQuery lands)

        # --- list operations ---
        assert (await arun(Portfolio.tags.first_elem(), ctx))[0] == "alpha"
        assert (await arun(Portfolio.tags.last_elem(), ctx))[0] == "epsilon"

        # --- set operations ---
        union = (await arun(Portfolio.members.union({"dave"}), ctx))[0]
        assert union == {"alice", "bob", "charlie", "dave"}

        # --- shape navigation ---
        assert (await arun(Portfolio.orders[0].symbol, ctx))[0] == "AAPL"
        assert (await arun(Portfolio.orders[1].price, ctx))[0] == 142.3

        # --- term composition ---
        total = Portfolio.orders[0].price * Portfolio.orders[0].qty
        assert (await arun(total, ctx))[0] == 1855.0

        spread = Portfolio.orders[0].price - Portfolio.orders[2].price
        assert abs((await arun(spread, ctx))[0] - (-59.5)) < 0.01

        # --- dict mutation ---
        await arun(Portfolio.metadata.set_item("sector", "tech"), ctx)
        assert (await arun(Portfolio.metadata.get_item("sector"), ctx))[0] == "tech"

        # --- list mutation ---
        await arun(Portfolio.tags.append("zeta"), ctx)
        assert (await arun(Portfolio.tags.last_elem(), ctx))[0] == "zeta"

        # --- set mutation ---
        await arun(Portfolio.members.add("eve"), ctx)
        result = (await arun(Portfolio.members, ctx))[0]
        assert "eve" in builtins.set(result)

        # --- fn combinators ---
        # SortedQuery is a StreamQuery — arun yields a stream; materialize it.
        sorted_stream = (await arun(SortedQuery(Portfolio.metadata.keys()), ctx))[0]
        sorted_keys = [k async for k in sorted_stream]
        assert sorted_keys == ["horizon", "risk", "sector", "strategy"]

        key_count = (await arun(LenQuery(Portfolio.metadata.keys()), ctx))[0]
        assert key_count == 4

        has_risk = (await arun(ContainsQuery(Portfolio.metadata.keys(), "risk"), ctx))[0]
        assert has_risk is True

        has_fake = (await arun(ContainsQuery(Portfolio.metadata.keys(), "fake"), ctx))[0]
        assert has_fake is False
