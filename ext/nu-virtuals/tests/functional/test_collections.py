"""Tests for eb-virtuals collection refs — DictRef, ListRef, SetRef, ShapeRef.

Verifies:
- Correct Value types from _wrap_* methods
- Lazy/eager facet switching
- Collection operations execute correctly through virtuals views
- Proper KeysView/ValuesView/ItemsView from virtuals
- Faceted execution produces correct results
"""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView

import pytest
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol

from nu_virtuals import (
    DictRef,
    FloatRef,
    IntRef,
    ListRef,
    SetRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
)
from nu_virtuals.refs.base import Facet
from nu import Context
from nu import (
    DictItemsI,
    DictKeysI,
    DictI,
    DictValuesI,
    IteratorI,
    ListI,
    SetI,
    fn,
)
from nu.shapes import Shape


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


# ============================================================================
# HELPERS
# ============================================================================


@pytest.fixture
def portfolio_ctx(nav, tx):
    """Context with Portfolio shape bindings."""
    return (
        Context()
        .bind(nav, Navigator)
        .bind(nav, Navigator, Portfolio)
        .bind(tx, TransactionProtocol)
        .bind(tx, TransactionProtocol, Portfolio)
    )


async def store(ref, value, ctx):
    await ref.store(value).execute(ctx)


# ============================================================================
# FACET TESTS — lazy/eager switching
# ============================================================================


class TestFacets:
    """Facet switching on ViewRef."""

    def test_default_facet_is_lazy(self):
        assert Portfolio.metadata._facet is Facet.LAZY

    def test_eager_property(self):
        eager = Portfolio.metadata.eager
        assert eager._facet is Facet.EAGER

    def test_lazy_property_noop(self):
        ref = Portfolio.metadata
        lazy = ref.lazy
        assert lazy is ref

    def test_eager_lazy_roundtrip(self):
        ref = Portfolio.metadata.eager.lazy
        assert ref._facet is Facet.LAZY

    def test_lazy_eager_roundtrip(self):
        ref = Portfolio.metadata.lazy.eager
        assert ref._facet is Facet.EAGER

    def test_eager_is_copy_not_same(self):
        ref = Portfolio.metadata
        eager = ref.eager
        assert eager is not ref
        assert eager._facet is Facet.EAGER
        assert ref._facet is Facet.LAZY

    def test_eager_eager_is_noop(self):
        eager1 = Portfolio.metadata.eager
        eager2 = eager1.eager
        assert eager2 is eager1

    def test_facet_on_list_ref(self):
        assert Portfolio.tags._facet is Facet.LAZY
        assert Portfolio.tags.eager._facet is Facet.EAGER

    def test_facet_on_set_ref(self):
        assert Portfolio.members._facet is Facet.LAZY
        assert Portfolio.members.eager._facet is Facet.EAGER


# ============================================================================
# DICT REF — wrapping types
# ============================================================================


class TestDictRefWrapTypes:
    """DictRef returns DictKeysI/DictValuesI/DictItemsI."""

    def test_keys_returns_dict_keys_value(self):
        keys = Portfolio.metadata.keys()
        assert isinstance(keys, DictKeysI)

    def test_values_returns_dict_values_value(self):
        vals = Portfolio.metadata.values()
        assert isinstance(vals, DictValuesI)

    def test_items_returns_dict_items_value(self):
        items = Portfolio.metadata.items()
        assert isinstance(items, DictItemsI)

    def test_result_returns_dict_value(self):
        from nu import ensure_nu

        result = Portfolio.metadata.result(ensure_nu("x"))
        assert isinstance(result, DictI)


class TestDictRefExecution:
    """DictRef operations produce correct results through virtuals."""

    @pytest.mark.asyncio
    async def test_store_and_keys(self, portfolio_ctx):
        await store(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = await Portfolio.metadata.keys().execute(portfolio_ctx)
        assert isinstance(result, KeysView)
        assert set(result) == {"strategy", "risk"}

    @pytest.mark.asyncio
    async def test_store_and_values(self, portfolio_ctx):
        await store(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = await Portfolio.metadata.values().execute(portfolio_ctx)
        assert isinstance(result, ValuesView)
        assert set(result) == {"momentum", "medium"}

    @pytest.mark.asyncio
    async def test_store_and_items(self, portfolio_ctx):
        await store(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = await Portfolio.metadata.items().execute(portfolio_ctx)
        assert isinstance(result, ItemsView)
        assert set(result) == {("strategy", "momentum"), ("risk", "medium")}

    @pytest.mark.asyncio
    async def test_get(self, portfolio_ctx):
        await store(Portfolio.metadata, {"key": "value"}, portfolio_ctx)
        result = await Portfolio.metadata.get("key").execute(portfolio_ctx)
        assert result == "value"

    @pytest.mark.asyncio
    async def test_set_item(self, portfolio_ctx):
        await store(Portfolio.metadata, {}, portfolio_ctx)
        await Portfolio.metadata.set("new_key", "new_val").execute(portfolio_ctx)
        result = await Portfolio.metadata.get("new_key").execute(portfolio_ctx)
        assert result == "new_val"


# ============================================================================
# LIST REF — iteration and slicing
# ============================================================================


class TestListRefWrapTypes:
    """ListRef wrapping types."""

    def test_iterable_is_iterator_value(self):
        from nu import ensure_nu

        wrapped = Portfolio.tags._wrap_iterable_result(ensure_nu("x"))
        assert isinstance(wrapped, IteratorI)

    def test_sliceable_is_list_value(self):
        from nu import ensure_nu

        wrapped = Portfolio.tags._wrap_sliceable_result(ensure_nu("x"))
        assert isinstance(wrapped, ListI)


class TestListRefExecution:
    """ListRef operations through virtuals."""

    @pytest.mark.asyncio
    async def test_store_and_first(self, portfolio_ctx):
        await store(Portfolio.tags, ["alpha", "beta", "gamma"], portfolio_ctx)
        result = await Portfolio.tags.first().execute(portfolio_ctx)
        assert result == "alpha"

    @pytest.mark.asyncio
    async def test_store_and_last(self, portfolio_ctx):
        await store(Portfolio.tags, ["alpha", "beta", "gamma"], portfolio_ctx)
        result = await Portfolio.tags.last().execute(portfolio_ctx)
        assert result == "gamma"

    @pytest.mark.asyncio
    async def test_store_and_slice(self, portfolio_ctx):
        await store(Portfolio.tags, ["a", "b", "c", "d", "e"], portfolio_ctx)
        result = await Portfolio.tags.slice(1, 3).execute(portfolio_ctx)
        assert list(result) == ["b", "c"]

    @pytest.mark.asyncio
    async def test_append(self, portfolio_ctx):
        await store(Portfolio.tags, ["x"], portfolio_ctx)
        await Portfolio.tags.append("y").execute(portfolio_ctx)
        result = await Portfolio.tags.execute(portfolio_ctx)
        assert list(result) == ["x", "y"]


# ============================================================================
# SET REF
# ============================================================================


class TestSetRefWrapTypes:
    """SetRef wrapping types."""

    def test_set_result_is_set_value(self):
        from nu import ensure_nu

        wrapped = Portfolio.members._wrap_set_result(ensure_nu("x"))
        assert isinstance(wrapped, SetI)


class TestSetRefExecution:
    """SetRef operations through virtuals."""

    @pytest.mark.asyncio
    async def test_store_and_add(self, portfolio_ctx):
        await store(Portfolio.members, {"alice"}, portfolio_ctx)
        await Portfolio.members.add("bob").execute(portfolio_ctx)
        result = await Portfolio.members.execute(portfolio_ctx)
        assert set(result) == {"alice", "bob"}

    @pytest.mark.asyncio
    async def test_union(self, portfolio_ctx):
        await store(Portfolio.members, {"alice", "bob"}, portfolio_ctx)
        result = await Portfolio.members.union({"bob", "charlie"}).execute(portfolio_ctx)
        assert result == {"alice", "bob", "charlie"}


# ============================================================================
# SHAPES LIST REF — sequence of shapes
# ============================================================================


class TestShapesListRefExecution:
    """ShapesListRef operations through virtuals."""

    @pytest.mark.asyncio
    async def test_store_and_navigate(self, portfolio_ctx):
        await store(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
            ],
            portfolio_ctx,
        )
        result = await Portfolio.orders[0].symbol.execute(portfolio_ctx)
        assert result == "AAPL"

    @pytest.mark.asyncio
    async def test_store_and_second_element(self, portfolio_ctx):
        await store(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
            ],
            portfolio_ctx,
        )
        result = await Portfolio.orders[1].price.execute(portfolio_ctx)
        assert result == 142.3


# ============================================================================
# SHAPES DICT REF — mapping of shapes
# ============================================================================


class TestShapesDictRefWrapTypes:
    """ShapesDictRef returns DictKeysI/DictValuesI/DictItemsI."""

    def test_keys_returns_dict_keys_value(self):
        keys = Portfolio.team.keys()
        assert isinstance(keys, DictKeysI)

    def test_values_returns_dict_values_value(self):
        vals = Portfolio.team.values()
        assert isinstance(vals, DictValuesI)

    def test_items_returns_dict_items_value(self):
        items = Portfolio.team.items()
        assert isinstance(items, DictItemsI)


class TestShapesDictRefExecution:
    """ShapesDictRef operations through virtuals."""

    @pytest.mark.asyncio
    async def test_store_and_keys(self, portfolio_ctx):
        await store(
            Portfolio.team,
            {
                "desk_a": {"symbol": "AAPL", "price": 185.5, "qty": 10},
                "desk_b": {"symbol": "GOOG", "price": 142.3, "qty": 5},
            },
            portfolio_ctx,
        )
        result = await Portfolio.team.keys().execute(portfolio_ctx)
        assert set(result) == {"desk_a", "desk_b"}

    @pytest.mark.asyncio
    async def test_slot_navigation(self, portfolio_ctx):
        await store(
            Portfolio.team,
            {
                "desk_a": {"symbol": "AAPL", "price": 185.5, "qty": 10},
            },
            portfolio_ctx,
        )
        result = await Portfolio.team["desk_a"].symbol.execute(portfolio_ctx)
        assert result == "AAPL"


# ============================================================================
# TERM COMPOSITION
# ============================================================================


class TestTermComposition:
    """Nu arithmetic across refs."""

    @pytest.mark.asyncio
    async def test_multiply(self, portfolio_ctx):
        await store(
            Portfolio.orders,
            [{"symbol": "AAPL", "price": 185.5, "qty": 10}],
            portfolio_ctx,
        )
        total = Portfolio.orders[0].price * Portfolio.orders[0].qty
        result = await total.execute(portfolio_ctx)
        assert result == 1855.0

    @pytest.mark.asyncio
    async def test_subtract(self, portfolio_ctx):
        await store(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
            ],
            portfolio_ctx,
        )
        spread = Portfolio.orders[0].price - Portfolio.orders[1].price
        result = await spread.execute(portfolio_ctx)
        assert abs(result - 43.2) < 0.01


# ============================================================================
# LAZY TAKE — islice over keys/values/items
# ============================================================================


class TestLazyTake:
    """fn.Take(keys, n) lazily slices collections via itertools.islice."""

    @pytest.mark.asyncio
    async def test_take_keys(self, portfolio_ctx):
        await store(Portfolio.metadata, {f"k{i}": f"v{i}" for i in range(50)}, portfolio_ctx)
        result = await fn.Take(Portfolio.metadata.keys(), 5).to_list().execute(portfolio_ctx)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_take_values(self, portfolio_ctx):
        await store(Portfolio.metadata, {f"k{i}": f"v{i}" for i in range(50)}, portfolio_ctx)
        result = await fn.Take(Portfolio.metadata.values(), 3).to_list().execute(portfolio_ctx)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_take_items(self, portfolio_ctx):
        await store(Portfolio.metadata, {"a": "1", "b": "2", "c": "3"}, portfolio_ctx)
        result = await fn.Take(Portfolio.metadata.items(), 2).to_list().execute(portfolio_ctx)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_take_list(self, portfolio_ctx):
        await store(Portfolio.tags, ["a", "b", "c", "d", "e"], portfolio_ctx)
        result = await fn.Take(Portfolio.tags, 3).to_list().execute(portfolio_ctx)
        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_take_more_than_available(self, portfolio_ctx):
        await store(Portfolio.metadata, {"a": "1", "b": "2"}, portfolio_ctx)
        result = await fn.Take(Portfolio.metadata.keys(), 100).to_list().execute(portfolio_ctx)
        assert sorted(result) == ["a", "b"]

    def test_take_returns_iterator_value(self):
        term = fn.Take(Portfolio.metadata.keys(), 10)
        assert isinstance(term, IteratorI)


# ============================================================================
# END-TO-END — full scenario through virtuals
# ============================================================================


class TestEndToEnd:
    """Full scenario: populate, navigate, query, mutate, compose."""

    @pytest.mark.asyncio
    async def test_full_scenario(self, portfolio_ctx):
        ctx = portfolio_ctx

        # --- populate ---
        await store(Portfolio.name, "Main Portfolio", ctx)
        await store(Portfolio.tags, ["alpha", "beta", "gamma", "delta", "epsilon"], ctx)
        await store(
            Portfolio.metadata, {"strategy": "momentum", "risk": "medium", "horizon": "long"}, ctx
        )
        await store(Portfolio.members, {"alice", "bob", "charlie"}, ctx)
        await store(
            Portfolio.orders,
            [
                {"symbol": "AAPL", "price": 185.5, "qty": 10},
                {"symbol": "GOOG", "price": 142.3, "qty": 5},
                {"symbol": "TSLA", "price": 245.0, "qty": 3},
            ],
            ctx,
        )

        # --- primitives ---
        assert await Portfolio.name.execute(ctx) == "Main Portfolio"

        # --- dict keys iteration ---
        keys = await Portfolio.metadata.keys().execute(ctx)
        assert set(keys) == {"strategy", "risk", "horizon"}

        # --- dict get ---
        assert await Portfolio.metadata.get("strategy").execute(ctx) == "momentum"

        # --- lazy Take over keys ---
        first_2 = await fn.Take(Portfolio.metadata.keys(), 2).to_list().execute(ctx)
        assert len(first_2) == 2

        # --- list operations ---
        assert await Portfolio.tags.first().execute(ctx) == "alpha"
        assert await Portfolio.tags.last().execute(ctx) == "epsilon"

        # --- lazy Take over list ---
        first_3 = await fn.Take(Portfolio.tags, 3).to_list().execute(ctx)
        assert first_3 == ["alpha", "beta", "gamma"]

        # --- set operations ---
        union = await Portfolio.members.union({"dave"}).execute(ctx)
        assert union == {"alice", "bob", "charlie", "dave"}

        # --- shape navigation ---
        assert await Portfolio.orders[0].symbol.execute(ctx) == "AAPL"
        assert await Portfolio.orders[1].price.execute(ctx) == 142.3

        # --- term composition ---
        total = Portfolio.orders[0].price * Portfolio.orders[0].qty
        assert await total.execute(ctx) == 1855.0

        spread = Portfolio.orders[0].price - Portfolio.orders[2].price
        assert abs(await spread.execute(ctx) - (-59.5)) < 0.01

        # --- dict mutation ---
        await Portfolio.metadata.set("sector", "tech").execute(ctx)
        assert await Portfolio.metadata.get("sector").execute(ctx) == "tech"

        # --- list mutation ---
        await Portfolio.tags.append("zeta").execute(ctx)
        assert await Portfolio.tags.last().execute(ctx) == "zeta"

        # --- set mutation ---
        await Portfolio.members.add("eve").execute(ctx)
        result = await Portfolio.members.execute(ctx)
        assert "eve" in set(result)

        # --- fn combinators ---
        sorted_keys = await fn.Sorted(Portfolio.metadata.keys()).execute(ctx)
        assert sorted_keys == ["horizon", "risk", "sector", "strategy"]

        key_count = await fn.Len(Portfolio.metadata.keys()).execute(ctx)
        assert key_count == 4

        has_risk = await fn.Contains(Portfolio.metadata.keys(), "risk").execute(ctx)
        assert has_risk is True

        has_fake = await fn.Contains(Portfolio.metadata.keys(), "fake").execute(ctx)
        assert has_fake is False
