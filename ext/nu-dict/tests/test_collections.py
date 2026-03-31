"""Tests for eb-dict collection refs — DictRef, ListRef, SetRef, ShapeRef.

Verifies:
- Correct Value types returned from _wrap_* methods
- keys/values/items produce DictKeysValue/DictValuesValue/DictItemsValue
- Execution produces correct Python results
- View operations (to_list, set operations on keys/items) work
- Lazy Take over keys (islice semantics)
- ListRef iteration vs slicing semantics
- End-to-end: shape navigation, term composition, fn combinators
"""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView

import pytest

from nu.abc import (
    AnyValue,
    DictItemsValue,
    DictKeysValue,
    DictValue,
    DictValuesValue,
    IteratorValue,
    ListValue,
    SetValue,
    fn,
)

from .conftest import PortfolioShape, TeamShape, UserShape


# ============================================================================
# DictRef — keys/values/items return proper view types
# ============================================================================


class TestDictRefViewTypes:
    """DictRef.keys/values/items return DictKeysValue/DictValuesValue/DictItemsValue."""

    def test_keys_returns_dict_keys_value(self):
        keys = PortfolioShape.metadata.keys()
        assert isinstance(keys, DictKeysValue)

    def test_values_returns_dict_values_value(self):
        vals = PortfolioShape.metadata.values()
        assert isinstance(vals, DictValuesValue)

    def test_items_returns_dict_items_value(self):
        items = PortfolioShape.metadata.items()
        assert isinstance(items, DictItemsValue)

    def test_result_returns_dict_value(self):
        from nu.abc import ensure_term

        result = PortfolioShape.metadata.result(ensure_term("dummy"))
        assert isinstance(result, DictValue)


class TestDictRefExecution:
    """DictRef collection ops execute correctly."""

    @pytest.mark.asyncio
    async def test_keys_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum", "risk": "medium"}
        result = await PortfolioShape.metadata.keys().execute(portfolio_ctx)
        assert isinstance(result, KeysView)
        assert set(result) == {"strategy", "risk"}

    @pytest.mark.asyncio
    async def test_values_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum", "risk": "medium"}
        result = await PortfolioShape.metadata.values().execute(portfolio_ctx)
        assert isinstance(result, ValuesView)
        assert set(result) == {"momentum", "medium"}

    @pytest.mark.asyncio
    async def test_items_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum", "risk": "medium"}
        result = await PortfolioShape.metadata.items().execute(portfolio_ctx)
        assert isinstance(result, ItemsView)
        assert set(result) == {("strategy", "momentum"), ("risk", "medium")}

    @pytest.mark.asyncio
    async def test_get_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum"}
        result = await PortfolioShape.metadata.get("strategy").execute(portfolio_ctx)
        assert result == "momentum"

    @pytest.mark.asyncio
    async def test_set_and_get(self, data, portfolio_ctx):
        data["metadata"] = {}
        await PortfolioShape.metadata.set("key", "value").execute(portfolio_ctx)
        assert data["metadata"]["key"] == "value"


class TestDictRefViewOperations:
    """DictKeysValue supports set-like operations, DictValuesValue supports materialization."""

    @pytest.mark.asyncio
    async def test_keys_to_list(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = await PortfolioShape.metadata.keys().to_list().execute(portfolio_ctx)
        assert sorted(result) == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_keys_to_set(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = await PortfolioShape.metadata.keys().to_set().execute(portfolio_ctx)
        assert result == {"a", "b", "c"}

    @pytest.mark.asyncio
    async def test_values_to_list(self, data, portfolio_ctx):
        data["metadata"] = {"a": "x", "b": "y"}
        result = await PortfolioShape.metadata.values().to_list().execute(portfolio_ctx)
        assert sorted(result) == ["x", "y"]

    @pytest.mark.asyncio
    async def test_items_to_list(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2}
        result = await PortfolioShape.metadata.items().to_list().execute(portfolio_ctx)
        assert sorted(result) == [("a", 1), ("b", 2)]

    @pytest.mark.asyncio
    async def test_keys_union(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2}
        result = await PortfolioShape.metadata.keys().union({"b", "c", "d"}).execute(portfolio_ctx)
        assert result == {"a", "b", "c", "d"}

    @pytest.mark.asyncio
    async def test_keys_intersection(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = (
            await PortfolioShape.metadata.keys()
            .intersection({"b", "c", "d"})
            .execute(portfolio_ctx)
        )
        assert result == {"b", "c"}

    @pytest.mark.asyncio
    async def test_keys_difference(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = await PortfolioShape.metadata.keys().difference({"b", "c"}).execute(portfolio_ctx)
        assert result == {"a"}

    @pytest.mark.asyncio
    async def test_items_union(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1}
        result = await PortfolioShape.metadata.items().union({("b", 2)}).execute(portfolio_ctx)
        assert result == {("a", 1), ("b", 2)}


# ============================================================================
# ListRef — iteration vs slicing
# ============================================================================


class TestListRefTypes:
    """ListRef wrapping types are correct."""

    def test_iterable_result_is_iterator_value(self):
        from nu.abc import ensure_term

        ref = PortfolioShape.tags
        wrapped = ref._wrap_iterable_result(ensure_term("dummy"))
        assert isinstance(wrapped, IteratorValue)

    def test_sliceable_result_is_list_value(self):
        from nu.abc import ensure_term

        ref = PortfolioShape.tags
        wrapped = ref._wrap_sliceable_result(ensure_term("dummy"))
        assert isinstance(wrapped, ListValue)

    def test_element_result_is_any_value(self):
        from nu.abc import ensure_term

        ref = PortfolioShape.tags
        wrapped = ref._wrap_element_result(ensure_term("dummy"))
        assert isinstance(wrapped, AnyValue)


class TestListRefExecution:
    """ListRef operations execute correctly."""

    @pytest.mark.asyncio
    async def test_first(self, data, portfolio_ctx):
        data["tags"] = ["alpha", "beta", "gamma"]
        result = await PortfolioShape.tags.first().execute(portfolio_ctx)
        assert result == "alpha"

    @pytest.mark.asyncio
    async def test_last(self, data, portfolio_ctx):
        data["tags"] = ["alpha", "beta", "gamma"]
        result = await PortfolioShape.tags.last().execute(portfolio_ctx)
        assert result == "gamma"

    @pytest.mark.asyncio
    async def test_slice(self, data, portfolio_ctx):
        data["tags"] = ["a", "b", "c", "d", "e"]
        result = await PortfolioShape.tags.slice(1, 3).execute(portfolio_ctx)
        assert result == ["b", "c"]

    @pytest.mark.asyncio
    async def test_append_and_read(self, data, portfolio_ctx):
        data["tags"] = ["x"]
        await PortfolioShape.tags.append("y").execute(portfolio_ctx)
        assert data["tags"] == ["x", "y"]


# ============================================================================
# SetRef — set operations
# ============================================================================


class TestSetRefTypes:
    """SetRef wrapping types are correct."""

    def test_set_result_is_set_value(self):
        from nu.abc import ensure_term

        ref = PortfolioShape.members
        wrapped = ref._wrap_set_result(ensure_term("dummy"))
        assert isinstance(wrapped, SetValue)

    def test_element_result_is_any_value(self):
        from nu.abc import ensure_term

        ref = PortfolioShape.members
        wrapped = ref._wrap_element_result(ensure_term("dummy"))
        assert isinstance(wrapped, AnyValue)


class TestSetRefExecution:
    """SetRef operations execute correctly."""

    @pytest.mark.asyncio
    async def test_add_and_contains(self, data, portfolio_ctx):
        data["members"] = {"alice"}
        await PortfolioShape.members.add("bob").execute(portfolio_ctx)
        assert data["members"] == {"alice", "bob"}

    @pytest.mark.asyncio
    async def test_union(self, data, portfolio_ctx):
        data["members"] = {"alice", "bob"}
        result = await PortfolioShape.members.union({"bob", "charlie"}).execute(portfolio_ctx)
        assert result == {"alice", "bob", "charlie"}


# ============================================================================
# ShapeRef — mapping view types on shape dicts
# ============================================================================


class TestShapeRefViewTypes:
    """ShapeRef returns proper view types for keys/values/items."""

    def test_keys_returns_dict_keys_value(self):
        info_ref = TeamShape.info
        keys = info_ref.keys()
        assert isinstance(keys, DictKeysValue)

    def test_values_returns_dict_values_value(self):
        info_ref = TeamShape.info
        vals = info_ref.values()
        assert isinstance(vals, DictValuesValue)

    def test_items_returns_dict_items_value(self):
        info_ref = TeamShape.info
        items = info_ref.items()
        assert isinstance(items, DictItemsValue)


class TestShapeRefExecution:
    """ShapeRef keys/values/items execute correctly."""

    @pytest.mark.asyncio
    async def test_shape_keys(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30, "score": 9.5}
        result = await TeamShape.info.keys().execute(team_ctx)
        assert set(result) == {"name", "age", "score"}

    @pytest.mark.asyncio
    async def test_shape_values(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30, "score": 9.5}
        result = await TeamShape.info.values().execute(team_ctx)
        assert set(result) == {"Alice", 30, 9.5}

    @pytest.mark.asyncio
    async def test_shape_items(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30}
        result = await TeamShape.info.items().execute(team_ctx)
        assert set(result) == {("name", "Alice"), ("age", 30)}

    @pytest.mark.asyncio
    async def test_shape_keys_to_list(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30}
        result = await TeamShape.info.keys().to_list().execute(team_ctx)
        assert sorted(result) == ["age", "name"]


# ============================================================================
# ShapesDictRef — mapping of shapes with view types
# ============================================================================


class TestShapesDictRefViewTypes:
    """ShapesDictRef returns proper view types."""

    def test_keys_returns_dict_keys_value(self):
        keys = TeamShape.members.keys()
        assert isinstance(keys, DictKeysValue)

    def test_values_returns_dict_values_value(self):
        vals = TeamShape.members.values()
        assert isinstance(vals, DictValuesValue)

    def test_items_returns_dict_items_value(self):
        items = TeamShape.members.items()
        assert isinstance(items, DictItemsValue)


class TestShapesDictRefExecution:
    """ShapesDictRef collection ops execute correctly."""

    @pytest.mark.asyncio
    async def test_keys(self, data, team_ctx):
        data["members"] = {
            "alice": {"name": "Alice", "age": 30, "score": 9.0},
            "bob": {"name": "Bob", "age": 25, "score": 8.5},
        }
        result = await TeamShape.members.keys().execute(team_ctx)
        assert set(result) == {"alice", "bob"}

    @pytest.mark.asyncio
    async def test_slot_navigation(self, data, team_ctx):
        data["members"] = {
            "alice": {"name": "Alice", "age": 30, "score": 9.0},
        }
        result = await TeamShape.members["alice"].name.execute(team_ctx)
        assert result == "Alice"


# ============================================================================
# Primitive refs — basic CRUD
# ============================================================================


class TestPrimitiveRefs:
    """Basic set/get on typed primitive refs."""

    @pytest.mark.asyncio
    async def test_int_ref(self, data, user_ctx):
        data["age"] = 25
        result = await UserShape.age.execute(user_ctx)
        assert result == 25

    @pytest.mark.asyncio
    async def test_str_ref(self, data, user_ctx):
        data["name"] = "Alice"
        result = await UserShape.name.execute(user_ctx)
        assert result == "Alice"

    @pytest.mark.asyncio
    async def test_float_ref(self, data, user_ctx):
        data["score"] = 9.5
        result = await UserShape.score.execute(user_ctx)
        assert result == 9.5


# ============================================================================
# Lazy Take — islice over keys/values/items
# ============================================================================


class TestLazyTake:
    """fn.Take(keys, n) lazily slices dict views via itertools.islice."""

    @pytest.mark.asyncio
    async def test_take_keys(self, data, portfolio_ctx):
        data["metadata"] = {f"key_{i}": f"val_{i}" for i in range(100)}
        result = await fn.Take(PortfolioShape.metadata.keys(), 3).to_list().execute(portfolio_ctx)
        assert len(result) == 3
        assert all(k.startswith("key_") for k in result)

    @pytest.mark.asyncio
    async def test_take_values(self, data, portfolio_ctx):
        data["metadata"] = {f"k{i}": f"v{i}" for i in range(50)}
        result = await fn.Take(PortfolioShape.metadata.values(), 5).to_list().execute(portfolio_ctx)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_take_items(self, data, portfolio_ctx):
        data["metadata"] = {f"k{i}": f"v{i}" for i in range(50)}
        result = await fn.Take(PortfolioShape.metadata.items(), 2).to_list().execute(portfolio_ctx)
        assert len(result) == 2
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    @pytest.mark.asyncio
    async def test_take_more_than_available(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2}
        result = await fn.Take(PortfolioShape.metadata.keys(), 100).to_list().execute(portfolio_ctx)
        assert sorted(result) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_take_list(self, data, portfolio_ctx):
        data["tags"] = ["a", "b", "c", "d", "e", "f", "g"]
        result = await fn.Take(PortfolioShape.tags, 3).to_list().execute(portfolio_ctx)
        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_take_returns_iterator_value(self):
        term = fn.Take(PortfolioShape.metadata.keys(), 10)
        assert isinstance(term, IteratorValue)


# ============================================================================
# End-to-end — full scenario with shapes, navigation, terms, fn combinators
# ============================================================================


class TestEndToEnd:
    """Full end-to-end scenario exercising the eb-dict substrate."""

    @pytest.fixture
    def e2e_data(self):
        return {}

    @pytest.fixture
    def e2e_ctx(self, e2e_data):
        from nu import Context

        return Context().bind(e2e_data, dict, PortfolioShape)

    @pytest.mark.asyncio
    async def test_full_scenario(self, e2e_data, e2e_ctx):
        d = e2e_data

        # populate
        d["title"] = "Main Portfolio"
        d["tags"] = ["alpha", "beta", "gamma", "delta", "epsilon"]
        d["metadata"] = {"strategy": "momentum", "risk": "medium", "horizon": "long"}
        d["members"] = {"alice", "bob", "charlie"}

        # --- primitives ---
        title = await PortfolioShape.title.execute(e2e_ctx)
        assert title == "Main Portfolio"

        # --- dict keys view (DictKeysValue) ---
        keys = await PortfolioShape.metadata.keys().execute(e2e_ctx)
        assert isinstance(keys, KeysView)
        assert set(keys) == {"strategy", "risk", "horizon"}

        # --- keys set operations ---
        common = (
            await PortfolioShape.metadata.keys().intersection({"risk", "alpha"}).execute(e2e_ctx)
        )
        assert common == {"risk"}

        # --- keys materialization ---
        key_list = await PortfolioShape.metadata.keys().to_list().execute(e2e_ctx)
        assert sorted(key_list) == ["horizon", "risk", "strategy"]

        key_set = await PortfolioShape.metadata.keys().to_set().execute(e2e_ctx)
        assert key_set == {"strategy", "risk", "horizon"}

        # --- dict values view ---
        vals = await PortfolioShape.metadata.values().execute(e2e_ctx)
        assert isinstance(vals, ValuesView)
        assert set(vals) == {"momentum", "medium", "long"}

        # --- dict items view ---
        items = await PortfolioShape.metadata.items().execute(e2e_ctx)
        assert isinstance(items, ItemsView)
        assert ("strategy", "momentum") in items

        # --- lazy Take over keys ---
        first_2 = await fn.Take(PortfolioShape.metadata.keys(), 2).to_list().execute(e2e_ctx)
        assert len(first_2) == 2

        # --- list operations ---
        first_tag = await PortfolioShape.tags.first().execute(e2e_ctx)
        assert first_tag == "alpha"

        last_tag = await PortfolioShape.tags.last().execute(e2e_ctx)
        assert last_tag == "epsilon"

        sliced = await PortfolioShape.tags.slice(1, 4).execute(e2e_ctx)
        assert sliced == ["beta", "gamma", "delta"]

        # --- lazy Take over list ---
        first_3_tags = await fn.Take(PortfolioShape.tags, 3).to_list().execute(e2e_ctx)
        assert first_3_tags == ["alpha", "beta", "gamma"]

        # --- set operations ---
        union = await PortfolioShape.members.union({"dave"}).execute(e2e_ctx)
        assert union == {"alice", "bob", "charlie", "dave"}

        # --- dict mutation ---
        await PortfolioShape.metadata.set("sector", "tech").execute(e2e_ctx)
        assert d["metadata"]["sector"] == "tech"

        sector = await PortfolioShape.metadata.get("sector").execute(e2e_ctx)
        assert sector == "tech"

        # --- list mutation ---
        await PortfolioShape.tags.append("zeta").execute(e2e_ctx)
        assert d["tags"][-1] == "zeta"

        # --- set mutation ---
        await PortfolioShape.members.add("eve").execute(e2e_ctx)
        assert "eve" in d["members"]

        # --- fn combinators ---
        sorted_keys = await fn.Sorted(PortfolioShape.metadata.keys()).execute(e2e_ctx)
        assert sorted_keys == ["horizon", "risk", "sector", "strategy"]

        key_count = await fn.Len(PortfolioShape.metadata.keys()).execute(e2e_ctx)
        assert key_count == 4

        has_risk = await fn.Contains(PortfolioShape.metadata.keys(), "risk").execute(e2e_ctx)
        assert has_risk is True

        has_fake = await fn.Contains(PortfolioShape.metadata.keys(), "fake").execute(e2e_ctx)
        assert has_fake is False


class TestEndToEndShapeNavigation:
    """End-to-end with nested shapes — ShapesDictRef, ShapesListRef, ShapeRef."""

    @pytest.fixture
    def nav_data(self):
        return {}

    @pytest.fixture
    def nav_ctx(self, nav_data):
        from nu import Context

        return Context().bind(nav_data, dict, TeamShape)

    @pytest.mark.asyncio
    async def test_nested_shapes(self, nav_data, nav_ctx):
        d = nav_data

        # populate shapes dict
        d["members"] = {
            "alice": {"name": "Alice", "age": 30, "score": 9.5},
            "bob": {"name": "Bob", "age": 25, "score": 8.0},
            "charlie": {"name": "Charlie", "age": 35, "score": 7.5},
        }

        # populate shapes list
        d["roster"] = [
            {"symbol": "AAPL", "price": 185.5, "qty": 10},
            {"symbol": "GOOG", "price": 142.3, "qty": 5},
            {"symbol": "TSLA", "price": 245.0, "qty": 3},
        ]

        # populate nested shape
        d["info"] = {"name": "Team Alpha", "age": 5, "score": 9.0}

        # --- ShapesDictRef navigation ---
        alice_name = await TeamShape.members["alice"].name.execute(nav_ctx)
        assert alice_name == "Alice"

        bob_age = await TeamShape.members["bob"].age.execute(nav_ctx)
        assert bob_age == 25

        # --- ShapesDictRef keys ---
        member_keys = await TeamShape.members.keys().execute(nav_ctx)
        assert set(member_keys) == {"alice", "bob", "charlie"}

        # --- Take first 2 member keys ---
        first_2 = await fn.Take(TeamShape.members.keys(), 2).to_list().execute(nav_ctx)
        assert len(first_2) == 2

        # --- ShapesListRef navigation ---
        sym0 = await TeamShape.roster[0].symbol.execute(nav_ctx)
        assert sym0 == "AAPL"

        price2 = await TeamShape.roster[2].price.execute(nav_ctx)
        assert price2 == 245.0

        # --- Term composition across shapes list ---
        total_0 = TeamShape.roster[0].price * TeamShape.roster[0].qty
        assert await total_0.execute(nav_ctx) == 1855.0

        spread = TeamShape.roster[0].price - TeamShape.roster[2].price
        result = await spread.execute(nav_ctx)
        assert abs(result - (-59.5)) < 0.01

        # --- ShapeRef (nested shape) ---
        team_name = await TeamShape.info.name.execute(nav_ctx)
        assert team_name == "Team Alpha"

        info_keys = await TeamShape.info.keys().execute(nav_ctx)
        assert set(info_keys) == {"name", "age", "score"}

        # --- keys set ops on nested shape ---
        common = await TeamShape.info.keys().intersection({"name", "foo"}).execute(nav_ctx)
        assert common == {"name"}
