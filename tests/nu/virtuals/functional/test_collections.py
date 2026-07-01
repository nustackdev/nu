"""Tests for nu-virtuals collection refs — DictRef, ListRef, SetRef, ShapeRef.

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
)
from nu.domains.shape import Shape
from nu.virtuals import (
    DictRef,
    FloatRef,
    IntRef,
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


async def store(ref, value, ctx):
    await arun(ref.store(value), ctx)


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
        result = Portfolio.metadata.result(LiteralQuery("x"))
        assert isinstance(result, DictForm)


class TestDictRefExecution:
    """DictRef operations produce correct results through virtuals."""

    @pytest.mark.asyncio
    async def test_store_and_keys(self, portfolio_ctx):
        await store(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = (await arun(Portfolio.metadata.keys(), portfolio_ctx))[0]
        assert isinstance(result, KeysView)
        assert set(result) == {"strategy", "risk"}

    @pytest.mark.asyncio
    async def test_store_and_values(self, portfolio_ctx):
        await store(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = (await arun(Portfolio.metadata.values(), portfolio_ctx))[0]
        assert isinstance(result, ValuesView)
        assert set(result) == {"momentum", "medium"}

    @pytest.mark.asyncio
    async def test_store_and_items(self, portfolio_ctx):
        await store(Portfolio.metadata, {"strategy": "momentum", "risk": "medium"}, portfolio_ctx)
        result = (await arun(Portfolio.metadata.items(), portfolio_ctx))[0]
        assert isinstance(result, ItemsView)
        assert set(result) == {("strategy", "momentum"), ("risk", "medium")}

    @pytest.mark.asyncio
    async def test_get(self, portfolio_ctx):
        await store(Portfolio.metadata, {"key": "value"}, portfolio_ctx)
        result = (await arun(Portfolio.metadata.get("key"), portfolio_ctx))[0]
        assert result == "value"

    @pytest.mark.asyncio
    async def test_set_item(self, portfolio_ctx):
        await store(Portfolio.metadata, {}, portfolio_ctx)
        await arun(Portfolio.metadata.set("new_key", "new_val"), portfolio_ctx)
        result = (await arun(Portfolio.metadata.get("new_key"), portfolio_ctx))[0]
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
    async def test_store_and_first(self, portfolio_ctx):
        await store(Portfolio.tags, ["alpha", "beta", "gamma"], portfolio_ctx)
        result = (await arun(Portfolio.tags.first_elem(), portfolio_ctx))[0]
        assert result == "alpha"

    @pytest.mark.asyncio
    async def test_store_and_last(self, portfolio_ctx):
        await store(Portfolio.tags, ["alpha", "beta", "gamma"], portfolio_ctx)
        result = (await arun(Portfolio.tags.last_elem(), portfolio_ctx))[0]
        assert result == "gamma"

    @pytest.mark.asyncio
    async def test_store_and_slice(self, portfolio_ctx):
        await store(Portfolio.tags, ["a", "b", "c", "d", "e"], portfolio_ctx)
        result = (await arun(Portfolio.tags.slice(1, 3), portfolio_ctx))[0]
        assert list(result) == ["b", "c"]

    @pytest.mark.asyncio
    async def test_append(self, portfolio_ctx):
        await store(Portfolio.tags, ["x"], portfolio_ctx)
        await arun(Portfolio.tags.append("y"), portfolio_ctx)
        result = (await arun(Portfolio.tags, portfolio_ctx))[0]
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

    @pytest.mark.asyncio
    async def test_store_and_add(self, portfolio_ctx):
        await store(Portfolio.members, {"alice"}, portfolio_ctx)
        await arun(Portfolio.members.add("bob"), portfolio_ctx)
        result = (await arun(Portfolio.members, portfolio_ctx))[0]
        assert set(result) == {"alice", "bob"}

    @pytest.mark.asyncio
    async def test_union(self, portfolio_ctx):
        await store(Portfolio.members, {"alice", "bob"}, portfolio_ctx)
        result = (await arun(Portfolio.members.union({"bob", "charlie"}), portfolio_ctx))[0]
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
        result = (await arun(Portfolio.orders[0].symbol, portfolio_ctx))[0]
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
        result = (await arun(Portfolio.orders[1].price, portfolio_ctx))[0]
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
        result = (await arun(Portfolio.team.keys(), portfolio_ctx))[0]
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
        result = (await arun(Portfolio.team["desk_a"].symbol, portfolio_ctx))[0]
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
        result = (await arun(total, portfolio_ctx))[0]
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
        result = (await arun(spread, portfolio_ctx))[0]
        assert abs(result - 43.2) < 0.01


# ============================================================================
# LAZY TAKE — islice over keys/values/items (deferred until TakeQuery lands)
# ============================================================================


@pytest.mark.skip(reason="TakeQuery not yet ported to v2")
class TestLazyTake:
    """Take(keys, n) lazily slices collections via itertools.islice."""

    @pytest.mark.asyncio
    async def test_take_keys(self, portfolio_ctx):
        await store(Portfolio.metadata, {f"k{i}": f"v{i}" for i in range(50)}, portfolio_ctx)
        result = (await arun(Take(Portfolio.metadata.keys(), 5).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_take_values(self, portfolio_ctx):
        await store(Portfolio.metadata, {f"k{i}": f"v{i}" for i in range(50)}, portfolio_ctx)
        result = (await arun(Take(Portfolio.metadata.values(), 3).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_take_items(self, portfolio_ctx):
        await store(Portfolio.metadata, {"a": "1", "b": "2", "c": "3"}, portfolio_ctx)
        result = (await arun(Take(Portfolio.metadata.items(), 2).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_take_list(self, portfolio_ctx):
        await store(Portfolio.tags, ["a", "b", "c", "d", "e"], portfolio_ctx)
        result = (await arun(Take(Portfolio.tags, 3).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_take_more_than_available(self, portfolio_ctx):
        await store(Portfolio.metadata, {"a": "1", "b": "2"}, portfolio_ctx)
        result = (await arun(Take(Portfolio.metadata.keys(), 100).to_list(), portfolio_ctx))[0]  # noqa: F821
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
        assert (await arun(Portfolio.name, ctx))[0] == "Main Portfolio"

        # --- dict keys iteration ---
        keys = (await arun(Portfolio.metadata.keys(), ctx))[0]
        assert set(keys) == {"strategy", "risk", "horizon"}

        # --- dict get ---
        assert (await arun(Portfolio.metadata.get("strategy"), ctx))[0] == "momentum"

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
        await arun(Portfolio.metadata.set("sector", "tech"), ctx)
        assert (await arun(Portfolio.metadata.get("sector"), ctx))[0] == "tech"

        # --- list mutation ---
        await arun(Portfolio.tags.append("zeta"), ctx)
        assert (await arun(Portfolio.tags.last_elem(), ctx))[0] == "zeta"

        # --- set mutation ---
        await arun(Portfolio.members.add("eve"), ctx)
        result = (await arun(Portfolio.members, ctx))[0]
        assert "eve" in set(result)

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
