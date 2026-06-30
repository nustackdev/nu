"""Tests for nu-mem collection refs — DictRef, ListRef, SetRef, ShapeRef.

Verifies:
- Correct Value types returned from _wrap_* methods
- keys/values/items produce DictKeysForm/DictValuesForm/DictItemsForm
- Execution produces correct Python results
- View operations (to_list, set operations on keys/items) work
- Lazy Take over keys (islice semantics)
- ListRef iteration vs slicing semantics
- End-to-end: shape navigation, term composition, fn combinators
"""

from __future__ import annotations

from collections.abc import ItemsView, KeysView, ValuesView

import pytest

from nu import (
    AnyForm,
    ContainsQuery,
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

from .conftest import PortfolioShape, TeamShape, UserShape


# ============================================================================
# DictRef — keys/values/items return proper view types
# ============================================================================


class TestDictRefViewTypes:
    """DictRef.keys/values/items return DictKeysForm/DictValuesForm/DictItemsForm."""

    def test_keys_returns_dict_keys_value(self):
        keys = PortfolioShape.metadata.keys()
        assert isinstance(keys, DictKeysForm)

    def test_values_returns_dict_values_value(self):
        vals = PortfolioShape.metadata.values()
        assert isinstance(vals, DictValuesForm)

    def test_items_returns_dict_items_value(self):
        items = PortfolioShape.metadata.items()
        assert isinstance(items, DictItemsForm)

    def test_result_returns_dict_value(self):
        result = PortfolioShape.metadata.result(LiteralQuery("dummy"))
        assert isinstance(result, DictForm)


class TestDictRefExecution:
    """DictRef collection ops execute correctly."""

    @pytest.mark.asyncio
    async def test_keys_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum", "risk": "medium"}
        result = (await arun(PortfolioShape.metadata.keys(), portfolio_ctx))[0]
        assert isinstance(result, KeysView)
        assert set(result) == {"strategy", "risk"}

    @pytest.mark.asyncio
    async def test_values_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum", "risk": "medium"}
        result = (await arun(PortfolioShape.metadata.values(), portfolio_ctx))[0]
        assert isinstance(result, ValuesView)
        assert set(result) == {"momentum", "medium"}

    @pytest.mark.asyncio
    async def test_items_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum", "risk": "medium"}
        result = (await arun(PortfolioShape.metadata.items(), portfolio_ctx))[0]
        assert isinstance(result, ItemsView)
        assert set(result) == {("strategy", "momentum"), ("risk", "medium")}

    @pytest.mark.asyncio
    async def test_get_execute(self, data, portfolio_ctx):
        data["metadata"] = {"strategy": "momentum"}
        result = (await arun(PortfolioShape.metadata.get("strategy"), portfolio_ctx))[0]
        assert result == "momentum"

    @pytest.mark.asyncio
    async def test_set_and_get(self, data, portfolio_ctx):
        data["metadata"] = {}
        await arun(PortfolioShape.metadata.set("key", "value"), portfolio_ctx)
        assert data["metadata"]["key"] == "value"


class TestDictRefViewOperations:
    """DictKeysForm supports set-like operations, DictValuesForm supports materialization."""

    @pytest.mark.asyncio
    async def test_keys_to_list(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = (await arun(PortfolioShape.metadata.keys().to_list(), portfolio_ctx))[0]
        assert sorted(result) == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_keys_to_set(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = (await arun(PortfolioShape.metadata.keys().to_set(), portfolio_ctx))[0]
        assert result == {"a", "b", "c"}

    @pytest.mark.asyncio
    async def test_values_to_list(self, data, portfolio_ctx):
        data["metadata"] = {"a": "x", "b": "y"}
        result = (await arun(PortfolioShape.metadata.values().to_list(), portfolio_ctx))[0]
        assert sorted(result) == ["x", "y"]

    @pytest.mark.asyncio
    async def test_items_to_list(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2}
        result = (await arun(PortfolioShape.metadata.items().to_list(), portfolio_ctx))[0]
        assert sorted(result) == [("a", 1), ("b", 2)]

    @pytest.mark.asyncio
    async def test_keys_union(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2}
        result = (
            await arun(PortfolioShape.metadata.keys().union({"b", "c", "d"}), portfolio_ctx)
        )[0]
        assert result == {"a", "b", "c", "d"}

    @pytest.mark.asyncio
    async def test_keys_intersection(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = (
            await arun(
                PortfolioShape.metadata.keys().intersection({"b", "c", "d"}), portfolio_ctx
            )
        )[0]
        assert result == {"b", "c"}

    @pytest.mark.asyncio
    async def test_keys_difference(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2, "c": 3}
        result = (
            await arun(PortfolioShape.metadata.keys().difference({"b", "c"}), portfolio_ctx)
        )[0]
        assert result == {"a"}

    @pytest.mark.asyncio
    async def test_items_union(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1}
        result = (
            await arun(PortfolioShape.metadata.items().union({("b", 2)}), portfolio_ctx)
        )[0]
        assert result == {("a", 1), ("b", 2)}


# ============================================================================
# ListRef — iteration vs slicing
# ============================================================================


class TestListRefTypes:
    """ListRef wrapping types are correct."""

    def test_iterable_result_is_iterator_value(self):
        ref = PortfolioShape.tags
        wrapped = ref._wrap_iterable_result(LiteralQuery("dummy"))
        assert isinstance(wrapped, IteratorForm)

    def test_sliceable_result_is_list_value(self):
        ref = PortfolioShape.tags
        wrapped = ref._wrap_sliceable_result(LiteralQuery("dummy"))
        assert isinstance(wrapped, ListForm)

    def test_element_result_is_any_value(self):
        ref = PortfolioShape.tags
        wrapped = ref._wrap_element_result(LiteralQuery("dummy"))
        assert isinstance(wrapped, AnyForm)


class TestListRefExecution:
    """ListRef operations execute correctly."""

    @pytest.mark.asyncio
    async def test_first(self, data, portfolio_ctx):
        data["tags"] = ["alpha", "beta", "gamma"]
        result = (await arun(PortfolioShape.tags.first_elem(), portfolio_ctx))[0]
        assert result == "alpha"

    @pytest.mark.asyncio
    async def test_last(self, data, portfolio_ctx):
        data["tags"] = ["alpha", "beta", "gamma"]
        result = (await arun(PortfolioShape.tags.last_elem(), portfolio_ctx))[0]
        assert result == "gamma"

    @pytest.mark.asyncio
    async def test_slice(self, data, portfolio_ctx):
        data["tags"] = ["a", "b", "c", "d", "e"]
        result = (await arun(PortfolioShape.tags.slice(1, 3), portfolio_ctx))[0]
        assert result == ["b", "c"]

    @pytest.mark.asyncio
    async def test_append_and_read(self, data, portfolio_ctx):
        data["tags"] = ["x"]
        await arun(PortfolioShape.tags.append("y"), portfolio_ctx)
        assert data["tags"] == ["x", "y"]


# ============================================================================
# SetRef — set operations
# ============================================================================


class TestSetRefTypes:
    """SetRef wrapping types are correct."""

    def test_set_result_is_set_value(self):
        ref = PortfolioShape.members
        wrapped = ref._wrap_set_result(LiteralQuery("dummy"))
        assert isinstance(wrapped, SetForm)

    def test_element_result_is_any_value(self):
        ref = PortfolioShape.members
        wrapped = ref._wrap_element_result(LiteralQuery("dummy"))
        assert isinstance(wrapped, AnyForm)


class TestSetRefExecution:
    """SetRef operations execute correctly."""

    @pytest.mark.asyncio
    async def test_add_and_contains(self, data, portfolio_ctx):
        data["members"] = {"alice"}
        await arun(PortfolioShape.members.add("bob"), portfolio_ctx)
        assert data["members"] == {"alice", "bob"}

    @pytest.mark.asyncio
    async def test_union(self, data, portfolio_ctx):
        data["members"] = {"alice", "bob"}
        result = (await arun(PortfolioShape.members.union({"bob", "charlie"}), portfolio_ctx))[0]
        assert result == {"alice", "bob", "charlie"}


# ============================================================================
# ShapeRef — mapping view types on shape dicts
# ============================================================================


class TestShapeRefViewTypes:
    """ShapeRef returns proper view types for keys/values/items."""

    def test_keys_returns_dict_keys_value(self):
        info_ref = TeamShape.info
        keys = info_ref.keys()
        assert isinstance(keys, DictKeysForm)

    def test_values_returns_dict_values_value(self):
        info_ref = TeamShape.info
        vals = info_ref.values()
        assert isinstance(vals, DictValuesForm)

    def test_items_returns_dict_items_value(self):
        info_ref = TeamShape.info
        items = info_ref.items()
        assert isinstance(items, DictItemsForm)


class TestShapeRefExecution:
    """ShapeRef keys/values/items execute correctly."""

    @pytest.mark.asyncio
    async def test_shape_keys(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30, "score": 9.5}
        result = (await arun(TeamShape.info.keys(), team_ctx))[0]
        assert set(result) == {"name", "age", "score"}

    @pytest.mark.asyncio
    async def test_shape_values(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30, "score": 9.5}
        result = (await arun(TeamShape.info.values(), team_ctx))[0]
        assert set(result) == {"Alice", 30, 9.5}

    @pytest.mark.asyncio
    async def test_shape_items(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30}
        result = (await arun(TeamShape.info.items(), team_ctx))[0]
        assert set(result) == {("name", "Alice"), ("age", 30)}

    @pytest.mark.asyncio
    async def test_shape_keys_to_list(self, data, team_ctx):
        data["info"] = {"name": "Alice", "age": 30}
        result = (await arun(TeamShape.info.keys().to_list(), team_ctx))[0]
        assert sorted(result) == ["age", "name"]


# ============================================================================
# ShapesDictRef — mapping of shapes with view types
# ============================================================================


class TestShapesDictRefViewTypes:
    """ShapesDictRef returns proper view types."""

    def test_keys_returns_dict_keys_value(self):
        keys = TeamShape.members.keys()
        assert isinstance(keys, DictKeysForm)

    def test_values_returns_dict_values_value(self):
        vals = TeamShape.members.values()
        assert isinstance(vals, DictValuesForm)

    def test_items_returns_dict_items_value(self):
        items = TeamShape.members.items()
        assert isinstance(items, DictItemsForm)


class TestShapesDictRefExecution:
    """ShapesDictRef collection ops execute correctly."""

    @pytest.mark.asyncio
    async def test_keys(self, data, team_ctx):
        data["members"] = {
            "alice": {"name": "Alice", "age": 30, "score": 9.0},
            "bob": {"name": "Bob", "age": 25, "score": 8.5},
        }
        result = (await arun(TeamShape.members.keys(), team_ctx))[0]
        assert set(result) == {"alice", "bob"}

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_slot_navigation(self, data, team_ctx):
        data["members"] = {
            "alice": {"name": "Alice", "age": 30, "score": 9.0},
        }
        result = (await arun(TeamShape.members["alice"].name, team_ctx))[0]
        assert result == "Alice"


# ============================================================================
# Primitive refs — basic CRUD
# ============================================================================


class TestPrimitiveRefs:
    """Basic set/get on typed primitive refs."""

    @pytest.mark.asyncio
    async def test_int_ref(self, data, user_ctx):
        data["age"] = 25
        result = (await arun(UserShape.age, user_ctx))[0]
        assert result == 25

    @pytest.mark.asyncio
    async def test_str_ref(self, data, user_ctx):
        data["name"] = "Alice"
        result = (await arun(UserShape.name, user_ctx))[0]
        assert result == "Alice"

    @pytest.mark.asyncio
    async def test_float_ref(self, data, user_ctx):
        data["score"] = 9.5
        result = (await arun(UserShape.score, user_ctx))[0]
        assert result == 9.5


# ============================================================================
# Lazy Take — islice over keys/values/items
# ============================================================================


@pytest.mark.skip(reason="TakeQuery not yet ported to v2")
class TestLazyTake:
    """Take(keys, n) lazily slices dict views via itertools.islice."""

    @pytest.mark.asyncio
    async def test_take_keys(self, data, portfolio_ctx):
        data["metadata"] = {f"key_{i}": f"val_{i}" for i in range(100)}
        result = (await arun(Take(PortfolioShape.metadata.keys(), 3).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert len(result) == 3
        assert all(k.startswith("key_") for k in result)

    @pytest.mark.asyncio
    async def test_take_values(self, data, portfolio_ctx):
        data["metadata"] = {f"k{i}": f"v{i}" for i in range(50)}
        result = (await arun(Take(PortfolioShape.metadata.values(), 5).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_take_items(self, data, portfolio_ctx):
        data["metadata"] = {f"k{i}": f"v{i}" for i in range(50)}
        result = (await arun(Take(PortfolioShape.metadata.items(), 2).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert len(result) == 2
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    @pytest.mark.asyncio
    async def test_take_more_than_available(self, data, portfolio_ctx):
        data["metadata"] = {"a": 1, "b": 2}
        result = (await arun(Take(PortfolioShape.metadata.keys(), 100).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert sorted(result) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_take_list(self, data, portfolio_ctx):
        data["tags"] = ["a", "b", "c", "d", "e", "f", "g"]
        result = (await arun(Take(PortfolioShape.tags, 3).to_list(), portfolio_ctx))[0]  # noqa: F821
        assert result == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_take_returns_iterator_value(self):
        term = Take(PortfolioShape.metadata.keys(), 10)  # noqa: F821
        assert isinstance(term, IteratorForm)


# ============================================================================
# End-to-end — full scenario with shapes, navigation, terms, fn combinators
# ============================================================================


class TestEndToEnd:
    """Full end-to-end scenario exercising the nu-mem substrate."""

    @pytest.fixture
    def e2e_data(self):
        return {}

    @pytest.fixture
    def e2e_ctx(self, e2e_data):
        from nu import Context

        return Context().bind(dict, e2e_data, PortfolioShape)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="TakeQuery not yet ported to v2 — scenario uses Take mid-body")
    async def test_full_scenario(self, e2e_data, e2e_ctx):
        d = e2e_data

        # populate
        d["title"] = "Main Portfolio"
        d["tags"] = ["alpha", "beta", "gamma", "delta", "epsilon"]
        d["metadata"] = {"strategy": "momentum", "risk": "medium", "horizon": "long"}
        d["members"] = {"alice", "bob", "charlie"}

        # --- primitives ---
        title = (await arun(PortfolioShape.title, e2e_ctx))[0]
        assert title == "Main Portfolio"

        # --- dict keys view (DictKeysForm) ---
        keys = (await arun(PortfolioShape.metadata.keys(), e2e_ctx))[0]
        assert isinstance(keys, KeysView)
        assert set(keys) == {"strategy", "risk", "horizon"}

        # --- keys set operations ---
        common = (
            await arun(PortfolioShape.metadata.keys().intersection({"risk", "alpha"}), e2e_ctx)
        )[0]
        assert common == {"risk"}

        # --- keys materialization ---
        key_list = (await arun(PortfolioShape.metadata.keys().to_list(), e2e_ctx))[0]
        assert sorted(key_list) == ["horizon", "risk", "strategy"]

        key_set = (await arun(PortfolioShape.metadata.keys().to_set(), e2e_ctx))[0]
        assert key_set == {"strategy", "risk", "horizon"}

        # --- dict values view ---
        vals = (await arun(PortfolioShape.metadata.values(), e2e_ctx))[0]
        assert isinstance(vals, ValuesView)
        assert set(vals) == {"momentum", "medium", "long"}

        # --- dict items view ---
        items = (await arun(PortfolioShape.metadata.items(), e2e_ctx))[0]
        assert isinstance(items, ItemsView)
        assert ("strategy", "momentum") in items

        # --- lazy Take over keys ---
        first_2 = (await arun(Take(PortfolioShape.metadata.keys(), 2).to_list(), e2e_ctx))[0]  # noqa: F821
        assert len(first_2) == 2

        # --- list operations ---
        first_tag = (await arun(PortfolioShape.tags.first_elem(), e2e_ctx))[0]
        assert first_tag == "alpha"

        last_tag = (await arun(PortfolioShape.tags.last_elem(), e2e_ctx))[0]
        assert last_tag == "epsilon"

        sliced = (await arun(PortfolioShape.tags.slice(1, 4), e2e_ctx))[0]
        assert sliced == ["beta", "gamma", "delta"]

        # --- lazy Take over list ---
        first_3_tags = (await arun(Take(PortfolioShape.tags, 3).to_list(), e2e_ctx))[0]  # noqa: F821
        assert first_3_tags == ["alpha", "beta", "gamma"]

        # --- set operations ---
        union = (await arun(PortfolioShape.members.union({"dave"}), e2e_ctx))[0]
        assert union == {"alice", "bob", "charlie", "dave"}

        # --- dict mutation ---
        await arun(PortfolioShape.metadata.set("sector", "tech"), e2e_ctx)
        assert d["metadata"]["sector"] == "tech"

        sector = (await arun(PortfolioShape.metadata.get("sector"), e2e_ctx))[0]
        assert sector == "tech"

        # --- list mutation ---
        await arun(PortfolioShape.tags.append("zeta"), e2e_ctx)
        assert d["tags"][-1] == "zeta"

        # --- set mutation ---
        await arun(PortfolioShape.members.add("eve"), e2e_ctx)
        assert "eve" in d["members"]

        # --- fn combinators ---
        sorted_keys = (await arun(SortedQuery(PortfolioShape.metadata.keys()), e2e_ctx))[0]
        assert sorted_keys == ["horizon", "risk", "sector", "strategy"]

        key_count = (await arun(LenQuery(PortfolioShape.metadata.keys()), e2e_ctx))[0]
        assert key_count == 4

        has_risk = (await arun(ContainsQuery(PortfolioShape.metadata.keys(), "risk"), e2e_ctx))[0]
        assert has_risk is True

        has_fake = (await arun(ContainsQuery(PortfolioShape.metadata.keys(), "fake"), e2e_ctx))[0]
        assert has_fake is False


class TestEndToEndShapeNavigation:
    """End-to-end with nested shapes — ShapesDictRef, ShapesListRef, ShapeRef."""

    @pytest.fixture
    def nav_data(self):
        return {}

    @pytest.fixture
    def nav_ctx(self, nav_data):
        from nu import Context

        return Context().bind(dict, nav_data, TeamShape)

    @pytest.mark.asyncio
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
        alice_name = (await arun(TeamShape.members["alice"].name, nav_ctx))[0]
        assert alice_name == "Alice"

        bob_age = (await arun(TeamShape.members["bob"].age, nav_ctx))[0]
        assert bob_age == 25

        # --- ShapesDictRef keys ---
        member_keys = (await arun(TeamShape.members.keys(), nav_ctx))[0]
        assert set(member_keys) == {"alice", "bob", "charlie"}

        # (lazy Take over keys covered in TestLazyTake — skipped until TakeQuery lands)

        # --- ShapesListRef navigation ---
        sym0 = (await arun(TeamShape.roster[0].symbol, nav_ctx))[0]
        assert sym0 == "AAPL"

        price2 = (await arun(TeamShape.roster[2].price, nav_ctx))[0]
        assert price2 == 245.0

        # --- Nu composition across shapes list ---
        total_0 = TeamShape.roster[0].price * TeamShape.roster[0].qty
        assert (await arun(total_0, nav_ctx))[0] == 1855.0

        spread = TeamShape.roster[0].price - TeamShape.roster[2].price
        result = (await arun(spread, nav_ctx))[0]
        assert abs(result - (-59.5)) < 0.01

        # --- ShapeRef (nested shape) ---
        team_name = (await arun(TeamShape.info.name, nav_ctx))[0]
        assert team_name == "Team Alpha"

        info_keys = (await arun(TeamShape.info.keys(), nav_ctx))[0]
        assert set(info_keys) == {"name", "age", "score"}

        # --- keys set ops on nested shape ---
        common = (await arun(TeamShape.info.keys().intersection({"name", "foo"}), nav_ctx))[0]
        assert common == {"name"}
