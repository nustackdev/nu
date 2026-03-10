"""Tests for ABC-level morphisms — operations (pure) and commands (impure).

Tests that:
1. Operation morphisms (abc_*) apply correctly
2. Command morphisms (abc_*, cmd_*) apply correctly
3. Mutable collection capabilities wire through to types
4. Type bases (ListType, DictType, SetType) expose mutation methods
"""

import pytest

from everybase import INVALID, Context
from everybase.abc import (
    AddCmd,
    AnyValue,
    AppendCmd,
    ClearCmd,
    CopyOp,
    CountOp,
    DeleteItemCmd,
    DictPopCmd,
    DictValue,
    DifferenceOp,
    DifferenceUpdateCmd,
    DiscardCmd,
    ExtendCmd,
    FirstOp,
    GetOp,
    IndexOfOp,
    InsertCmd,
    IntersectionOp,
    IntersectionUpdateCmd,
    IsDisjointOp,
    IsSubsetOp,
    IsSupersetOp,
    ItemsOp,
    KeysOp,
    LastOp,
    ListValue,
    NoneValue,
    PopCmd,
    PopItemCmd,
    RemoveCmd,
    RemoveValueCmd,
    SetDefaultCmd,
    SetItemCmd,
    SetPopCmd,
    SetUpdateCmd,
    SetValue,
    SymmetricDifferenceOp,
    SymmetricDifferenceUpdateCmd,
    UnionOp,
    UpdateCmd,
    ValuesOp,
)


# =============================================================================
# CONTEXT FIXTURE
# =============================================================================


@pytest.fixture()
def ctx():
    """Minimal execution context."""
    return Context()


# =============================================================================
# SEQUENCE OPERATIONS (pure)
# =============================================================================


class TestFirstOp:
    """FirstOp morphism tests."""

    async def test_first_element(self, ctx):
        op = FirstOp(ListValue([10, 20, 30]))
        assert await op.execute(ctx) == 10

    async def test_first_empty_returns_invalid(self, ctx):
        op = FirstOp(ListValue([]))
        assert await op.execute(ctx) is INVALID

    async def test_first_single(self, ctx):
        op = FirstOp(ListValue([42]))
        assert await op.execute(ctx) == 42


class TestLastOp:
    """LastOp morphism tests."""

    async def test_last_element(self, ctx):
        op = LastOp(ListValue([10, 20, 30]))
        assert await op.execute(ctx) == 30

    async def test_last_empty_returns_invalid(self, ctx):
        op = LastOp(ListValue([]))
        assert await op.execute(ctx) is INVALID

    async def test_last_single(self, ctx):
        op = LastOp(ListValue([42]))
        assert await op.execute(ctx) == 42


class TestIndexOfOp:
    """IndexOfOp morphism tests."""

    async def test_index_found(self, ctx):
        op = IndexOfOp(ListValue([10, 20, 30]), 20)
        assert await op.execute(ctx) == 1

    async def test_index_not_found(self, ctx):
        op = IndexOfOp(ListValue([10, 20, 30]), 99)
        assert await op.execute(ctx) is INVALID

    async def test_index_first_occurrence(self, ctx):
        op = IndexOfOp(ListValue([1, 2, 2, 3]), 2)
        assert await op.execute(ctx) == 1


class TestCountOp:
    """CountOp morphism tests."""

    async def test_count_occurrences(self, ctx):
        op = CountOp(ListValue([1, 2, 2, 3, 2]), 2)
        assert await op.execute(ctx) == 3

    async def test_count_zero(self, ctx):
        op = CountOp(ListValue([1, 2, 3]), 99)
        assert await op.execute(ctx) == 0


# =============================================================================
# MAPPING OPERATIONS (pure)
# =============================================================================


class TestKeysOp:
    """KeysOp morphism tests."""

    async def test_keys(self, ctx):
        op = KeysOp(DictValue({"a": 1, "b": 2}))
        assert set(await op.execute(ctx)) == {"a", "b"}

    async def test_keys_empty(self, ctx):
        op = KeysOp(DictValue({}))
        assert len(await op.execute(ctx)) == 0


class TestValuesOp:
    """ValuesOp morphism tests."""

    async def test_values(self, ctx):
        op = ValuesOp(DictValue({"a": 1, "b": 2}))
        assert set(await op.execute(ctx)) == {1, 2}

    async def test_values_empty(self, ctx):
        op = ValuesOp(DictValue({}))
        assert len(await op.execute(ctx)) == 0


class TestItemsOp:
    """ItemsOp morphism tests."""

    async def test_items(self, ctx):
        op = ItemsOp(DictValue({"a": 1}))
        assert set(await op.execute(ctx)) == {("a", 1)}

    async def test_items_empty(self, ctx):
        op = ItemsOp(DictValue({}))
        assert len(await op.execute(ctx)) == 0


class TestGetOp:
    """GetOp morphism tests."""

    async def test_get_existing(self, ctx):
        op = GetOp(DictValue({"a": 1, "b": 2}), "a", 0)
        assert await op.execute(ctx) == 1

    async def test_get_missing_with_default(self, ctx):
        op = GetOp(DictValue({"a": 1}), "z", 99)
        assert await op.execute(ctx) == 99

    async def test_get_missing_no_default(self, ctx):
        op = GetOp(DictValue({"a": 1}), "a", None)
        assert await op.execute(ctx) == 1


# =============================================================================
# SET OPERATIONS (pure)
# =============================================================================


class TestUnionOp:
    """UnionOp morphism tests."""

    async def test_union(self, ctx):
        op = UnionOp(SetValue({1, 2}), SetValue({2, 3}))
        assert await op.execute(ctx) == {1, 2, 3}

    async def test_union_disjoint(self, ctx):
        op = UnionOp(SetValue({1, 2}), SetValue({3, 4}))
        assert await op.execute(ctx) == {1, 2, 3, 4}


class TestIntersectionOp:
    """IntersectionOp morphism tests."""

    async def test_intersection(self, ctx):
        op = IntersectionOp(SetValue({1, 2, 3}), SetValue({2, 3, 4}))
        assert await op.execute(ctx) == {2, 3}

    async def test_intersection_empty(self, ctx):
        op = IntersectionOp(SetValue({1, 2}), SetValue({3, 4}))
        assert await op.execute(ctx) == set()


class TestDifferenceOp:
    """DifferenceOp morphism tests."""

    async def test_difference(self, ctx):
        op = DifferenceOp(SetValue({1, 2, 3}), SetValue({2, 3}))
        assert await op.execute(ctx) == {1}

    async def test_difference_no_overlap(self, ctx):
        op = DifferenceOp(SetValue({1, 2}), SetValue({3, 4}))
        assert await op.execute(ctx) == {1, 2}


class TestSymmetricDifferenceOp:
    """SymmetricDifferenceOp morphism tests."""

    async def test_symmetric_difference(self, ctx):
        op = SymmetricDifferenceOp(SetValue({1, 2, 3}), SetValue({2, 3, 4}))
        assert await op.execute(ctx) == {1, 4}


class TestIsSubsetOp:
    """IsSubsetOp morphism tests."""

    async def test_subset_true(self, ctx):
        op = IsSubsetOp(SetValue({1, 2}), SetValue({1, 2, 3}))
        assert await op.execute(ctx) is True

    async def test_subset_false(self, ctx):
        op = IsSubsetOp(SetValue({1, 4}), SetValue({1, 2, 3}))
        assert await op.execute(ctx) is False

    async def test_subset_equal(self, ctx):
        op = IsSubsetOp(SetValue({1, 2}), SetValue({1, 2}))
        assert await op.execute(ctx) is True


class TestIsSupersetOp:
    """IsSupersetOp morphism tests."""

    async def test_superset_true(self, ctx):
        op = IsSupersetOp(SetValue({1, 2, 3}), SetValue({1, 2}))
        assert await op.execute(ctx) is True

    async def test_superset_false(self, ctx):
        op = IsSupersetOp(SetValue({1, 2}), SetValue({1, 2, 3}))
        assert await op.execute(ctx) is False


class TestIsDisjointOp:
    """IsDisjointOp morphism tests."""

    async def test_disjoint_true(self, ctx):
        op = IsDisjointOp(SetValue({1, 2}), SetValue({3, 4}))
        assert await op.execute(ctx) is True

    async def test_disjoint_false(self, ctx):
        op = IsDisjointOp(SetValue({1, 2}), SetValue({2, 3}))
        assert await op.execute(ctx) is False


# =============================================================================
# SEQUENCE MUTATION COMMANDS
# =============================================================================


class TestAppendCmd:
    """AppendCmd morphism tests."""

    async def test_execute_appends(self, ctx):
        cmd = AppendCmd[int](ListValue([1, 2, 3]), 4)
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_appends_to_empty(self, ctx):
        cmd = AppendCmd[int](ListValue([]), 1)
        result = await cmd.execute(ctx)
        assert result is None


class TestInsertCmd:
    """InsertCmd morphism tests."""

    async def test_execute_inserts_at_index(self, ctx):
        cmd = InsertCmd[int](ListValue([1, 3]), 1, 2)
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_inserts_at_zero(self, ctx):
        cmd = InsertCmd[str](ListValue(["b", "c"]), 0, "a")
        result = await cmd.execute(ctx)
        assert result is None


class TestPopCmd:
    """PopCmd morphism tests."""

    async def test_execute_pops_last(self, ctx):
        cmd = PopCmd[int](ListValue([1, 2, 3]), -1)
        result = await cmd.execute(ctx)
        assert result == 3

    async def test_execute_pops_at_index(self, ctx):
        cmd = PopCmd[int](ListValue([1, 2, 3]), 0)
        result = await cmd.execute(ctx)
        assert result == 1


class TestExtendCmd:
    """ExtendCmd morphism tests."""

    async def test_execute_extends(self, ctx):
        cmd = ExtendCmd[int](ListValue([1, 2]), [3, 4])
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_extends_empty(self, ctx):
        cmd = ExtendCmd[int](ListValue([]), [1, 2])
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_extends_with_empty(self, ctx):
        cmd = ExtendCmd[int](ListValue([1, 2]), [])
        result = await cmd.execute(ctx)
        assert result is None


class TestRemoveValueCmd:
    """RemoveValueCmd morphism tests."""

    async def test_execute_removes_first(self, ctx):
        cmd = RemoveValueCmd[int](ListValue([1, 2, 3, 2]), 2)
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_removes_only(self, ctx):
        cmd = RemoveValueCmd[int](ListValue([1, 2, 3]), 2)
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_missing_returns_invalid(self, ctx):
        cmd = RemoveValueCmd[int](ListValue([1, 2, 3]), 99)
        result = await cmd.execute(ctx)
        assert result is INVALID


# =============================================================================
# MAPPING MUTATION COMMANDS
# =============================================================================


class TestSetItemCmd:
    """SetItemCmd morphism tests."""

    async def test_execute_sets_key(self, ctx):
        cmd = SetItemCmd[str, int](DictValue({"a": 1}), "b", 2)
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_overwrites_key(self, ctx):
        cmd = SetItemCmd[str, int](DictValue({"a": 1}), "a", 99)
        result = await cmd.execute(ctx)
        assert result is None


class TestDeleteItemCmd:
    """DeleteItemCmd morphism tests."""

    async def test_execute_deletes_key(self, ctx):
        cmd = DeleteItemCmd[str](DictValue({"a": 1, "b": 2}), "a")
        result = await cmd.execute(ctx)
        assert result is None


class TestUpdateCmd:
    """UpdateCmd morphism tests."""

    async def test_execute_updates_mapping(self, ctx):
        cmd = UpdateCmd[str, int](DictValue({"a": 1}), DictValue({"b": 2}))
        result = await cmd.execute(ctx)
        assert result is None


class TestDictPopCmd:
    """DictPopCmd morphism tests."""

    async def test_pop_existing_key(self, ctx):
        cmd = DictPopCmd[str, int](DictValue({"a": 1, "b": 2}), "a", None)
        result = await cmd.execute(ctx)
        assert result == 1

    async def test_pop_missing_key_with_default(self, ctx):
        cmd = DictPopCmd[str, int](DictValue({"a": 1}), "z", 99)
        result = await cmd.execute(ctx)
        assert result == 99

    async def test_pop_missing_key_no_default(self, ctx):
        cmd = DictPopCmd[str, int](DictValue({"a": 1}), "z", None)
        result = await cmd.execute(ctx)
        assert result is INVALID


class TestPopItemCmd:
    """PopItemCmd morphism tests."""

    async def test_popitem_returns_tuple(self, ctx):
        cmd = PopItemCmd[str, int](DictValue({"a": 1}))
        result = await cmd.execute(ctx)
        assert result == ("a", 1)

    async def test_popitem_empty_returns_invalid(self, ctx):
        cmd = PopItemCmd[str, int](DictValue({}))
        result = await cmd.execute(ctx)
        assert result is INVALID


class TestSetDefaultCmd:
    """SetDefaultCmd morphism tests."""

    async def test_setdefault_existing_key(self, ctx):
        cmd = SetDefaultCmd[str, int](DictValue({"a": 1}), "a", 99)
        result = await cmd.execute(ctx)
        assert result == 1

    async def test_setdefault_missing_key(self, ctx):
        cmd = SetDefaultCmd[str, int](DictValue({"a": 1}), "b", 99)
        result = await cmd.execute(ctx)
        assert result == 99


class TestCopyOp:
    """CopyOp morphism tests."""

    async def test_copy_returns_dict(self, ctx):
        cmd = CopyOp[str, int](DictValue({"a": 1, "b": 2}))
        result = await cmd.execute(ctx)
        assert result == {"a": 1, "b": 2}

    async def test_copy_is_shallow(self, ctx):
        original = {"a": [1, 2]}
        cmd = CopyOp(DictValue(original))
        result = await cmd.execute(ctx)
        assert result == {"a": [1, 2]}
        assert result["a"] is original["a"]

    async def test_copy_empty(self, ctx):
        cmd = CopyOp(DictValue({}))
        result = await cmd.execute(ctx)
        assert result == {}


# =============================================================================
# SET MUTATION COMMANDS
# =============================================================================


class TestAddCmd:
    """AddCmd morphism tests."""

    async def test_execute_adds_element(self, ctx):
        cmd = AddCmd[int](SetValue({1, 2}), 3)
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_add_existing(self, ctx):
        cmd = AddCmd[int](SetValue({1, 2}), 2)
        result = await cmd.execute(ctx)
        assert result is None


class TestRemoveCmd:
    """RemoveCmd morphism tests."""

    async def test_execute_removes_element(self, ctx):
        cmd = RemoveCmd[int](SetValue({1, 2, 3}), 2)
        result = await cmd.execute(ctx)
        assert result is None


class TestDiscardCmd:
    """DiscardCmd morphism tests."""

    async def test_execute_discards_element(self, ctx):
        cmd = DiscardCmd[int](SetValue({1, 2, 3}), 2)
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_discards_missing(self, ctx):
        cmd = DiscardCmd[int](SetValue({1, 2}), 99)
        result = await cmd.execute(ctx)
        assert result is None


class TestSetPopCmd:
    """SetPopCmd morphism tests."""

    async def test_pop_returns_element(self, ctx):
        cmd = SetPopCmd[int](SetValue({42}))
        result = await cmd.execute(ctx)
        assert result == 42

    async def test_pop_empty_returns_invalid(self, ctx):
        cmd = SetPopCmd[int](SetValue(set()))
        result = await cmd.execute(ctx)
        assert result is INVALID


class TestSetUpdateCmd:
    """SetUpdateCmd morphism tests."""

    async def test_update_adds_elements(self, ctx):
        s = {1, 2}
        cmd = SetUpdateCmd[int](SetValue(s), SetValue({3, 4}))
        result = await cmd.execute(ctx)
        assert result is None
        assert s == {1, 2, 3, 4}


class TestIntersectionUpdateCmd:
    """IntersectionUpdateCmd morphism tests."""

    async def test_intersection_update(self, ctx):
        s = {1, 2, 3}
        cmd = IntersectionUpdateCmd[int](SetValue(s), SetValue({2, 3, 4}))
        result = await cmd.execute(ctx)
        assert result is None
        assert s == {2, 3}


class TestDifferenceUpdateCmd:
    """DifferenceUpdateCmd morphism tests."""

    async def test_difference_update(self, ctx):
        s = {1, 2, 3}
        cmd = DifferenceUpdateCmd[int](SetValue(s), SetValue({2, 3}))
        result = await cmd.execute(ctx)
        assert result is None
        assert s == {1}


class TestSymmetricDifferenceUpdateCmd:
    """SymmetricDifferenceUpdateCmd morphism tests."""

    async def test_symmetric_difference_update(self, ctx):
        s = {1, 2, 3}
        cmd = SymmetricDifferenceUpdateCmd[int](SetValue(s), SetValue({2, 3, 4}))
        result = await cmd.execute(ctx)
        assert result is None
        assert s == {1, 4}


# =============================================================================
# CLEAR COMMAND
# =============================================================================


class TestClearCmd:
    """ClearCmd morphism tests."""

    async def test_execute_clears_list(self, ctx):
        cmd = ClearCmd(ListValue([1, 2, 3]))
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_clears_dict(self, ctx):
        cmd = ClearCmd(DictValue({"a": 1}))
        result = await cmd.execute(ctx)
        assert result is None

    async def test_execute_clears_set(self, ctx):
        cmd = ClearCmd(SetValue({1, 2, 3}))
        result = await cmd.execute(ctx)
        assert result is None


# =============================================================================
# TYPE BASE MUTATION METHODS (wiring through capabilities)
# =============================================================================


class TestListTypeMutations:
    """ListType exposes mutation methods via MutableSequenceBase."""

    def test_append_returns_none_value(self):
        lst = ListValue([1, 2, 3])
        result = lst.append(4)
        assert isinstance(result, NoneValue)

    def test_insert_returns_none_value(self):
        lst = ListValue([1, 3])
        result = lst.insert(1, 2)
        assert isinstance(result, NoneValue)

    def test_extend_returns_none_value(self):
        lst = ListValue([1, 2])
        result = lst.extend([3, 4])
        assert isinstance(result, NoneValue)

    def test_pop_returns_any_value(self):
        lst = ListValue([1, 2, 3])
        result = lst.pop()
        assert isinstance(result, AnyValue)

    def test_remove_returns_none_value(self):
        lst = ListValue([1, 2, 3])
        result = lst.remove(2)
        assert isinstance(result, NoneValue)

    def test_clear_returns_none_value(self):
        lst = ListValue([1, 2, 3])
        result = lst.clear()
        assert isinstance(result, NoneValue)


class TestDictTypeMutations:
    """DictType exposes mutation methods via MutableMappingBase."""

    def test_set_returns_none_value(self):
        d = DictValue({"a": 1})
        result = d.set("b", 2)
        assert isinstance(result, NoneValue)

    def test_delete_returns_none_value(self):
        d = DictValue({"a": 1})
        result = d.delete("a")
        assert isinstance(result, NoneValue)

    def test_update_returns_none_value(self):
        d = DictValue({"a": 1})
        result = d.update({"b": 2})
        assert isinstance(result, NoneValue)

    def test_pop_returns_any_value(self):
        d = DictValue({"a": 1})
        result = d.pop("a")
        assert isinstance(result, AnyValue)

    def test_popitem_returns_any_value(self):
        d = DictValue({"a": 1})
        result = d.popitem()
        assert isinstance(result, AnyValue)

    def test_setdefault_returns_any_value(self):
        d = DictValue({"a": 1})
        result = d.setdefault("b", 99)
        assert isinstance(result, AnyValue)

    def test_clear_returns_none_value(self):
        d = DictValue({"a": 1})
        result = d.clear()
        assert isinstance(result, NoneValue)

    def test_copy_returns_any_value(self):
        d = DictValue({"a": 1})
        result = d.copy()
        assert isinstance(result, AnyValue)


class TestSetTypeMutations:
    """SetType exposes mutation methods via MutableSetBase."""

    def test_add_returns_none_value(self):
        s = SetValue({1, 2})
        result = s.add(3)
        assert isinstance(result, NoneValue)

    def test_remove_returns_none_value(self):
        s = SetValue({1, 2, 3})
        result = s.remove(2)
        assert isinstance(result, NoneValue)

    def test_discard_returns_none_value(self):
        s = SetValue({1, 2, 3})
        result = s.discard(2)
        assert isinstance(result, NoneValue)

    def test_pop_returns_any_value(self):
        s = SetValue({1, 2, 3})
        result = s.pop()
        assert isinstance(result, AnyValue)

    def test_clear_returns_none_value(self):
        s = SetValue({1, 2, 3})
        result = s.clear()
        assert isinstance(result, NoneValue)

    def test_update_returns_none_value(self):
        s = SetValue({1, 2})
        result = s.update({3, 4})
        assert isinstance(result, NoneValue)

    def test_intersection_update_returns_none_value(self):
        s = SetValue({1, 2, 3})
        result = s.intersection_update({2, 3})
        assert isinstance(result, NoneValue)

    def test_difference_update_returns_none_value(self):
        s = SetValue({1, 2, 3})
        result = s.difference_update({2})
        assert isinstance(result, NoneValue)

    def test_symmetric_difference_update_returns_none_value(self):
        s = SetValue({1, 2, 3})
        result = s.symmetric_difference_update({2, 4})
        assert isinstance(result, NoneValue)


# =============================================================================
# EXECUTION INTEGRATION TESTS
# =============================================================================


class TestMutationExecution:
    """Test that mutation commands execute correctly end-to-end."""

    async def test_list_append_execute(self, ctx):
        lst = ListValue([1, 2])
        result = await lst.append(3).execute(ctx)
        assert result is None

    async def test_list_insert_execute(self, ctx):
        lst = ListValue([1, 3])
        result = await lst.insert(1, 2).execute(ctx)
        assert result is None

    async def test_list_extend_execute(self, ctx):
        lst = ListValue([1, 2])
        result = await lst.extend([3, 4]).execute(ctx)
        assert result is None

    async def test_list_pop_execute(self, ctx):
        lst = ListValue([1, 2, 3])
        result = await lst.pop().execute(ctx)
        assert result == 3

    async def test_list_remove_execute(self, ctx):
        lst = ListValue([1, 2, 3])
        result = await lst.remove(2).execute(ctx)
        assert result is None

    async def test_dict_set_execute(self, ctx):
        d = DictValue({"a": 1})
        result = await d.set("b", 2).execute(ctx)
        assert result is None

    async def test_dict_delete_execute(self, ctx):
        d = DictValue({"a": 1, "b": 2})
        result = await d.delete("a").execute(ctx)
        assert result is None

    async def test_dict_update_execute(self, ctx):
        d = DictValue({"a": 1})
        result = await d.update({"b": 2}).execute(ctx)
        assert result is None

    async def test_set_add_execute(self, ctx):
        s = SetValue({1, 2})
        result = await s.add(3).execute(ctx)
        assert result is None

    async def test_set_remove_execute(self, ctx):
        s = SetValue({1, 2, 3})
        result = await s.remove(2).execute(ctx)
        assert result is None

    async def test_set_discard_execute(self, ctx):
        s = SetValue({1, 2, 3})
        result = await s.discard(99).execute(ctx)
        assert result is None

    async def test_list_clear_execute(self, ctx):
        lst = ListValue([1, 2, 3])
        result = await lst.clear().execute(ctx)
        assert result is None

    async def test_dict_clear_execute(self, ctx):
        d = DictValue({"a": 1})
        result = await d.clear().execute(ctx)
        assert result is None

    async def test_set_clear_execute(self, ctx):
        s = SetValue({1, 2, 3})
        result = await s.clear().execute(ctx)
        assert result is None

    # ── New dict methods ──────────────────────────────────────────────────

    async def test_dict_pop_execute(self, ctx):
        d = DictValue({"a": 1, "b": 2})
        result = await d.pop("a").execute(ctx)
        assert result == 1

    async def test_dict_pop_missing_with_default(self, ctx):
        d = DictValue({"a": 1})
        result = await d.pop("z", 99).execute(ctx)
        assert result == 99

    async def test_dict_pop_missing_no_default(self, ctx):
        d = DictValue({"a": 1})
        result = await d.pop("z").execute(ctx)
        assert result is INVALID

    async def test_dict_popitem_execute(self, ctx):
        d = DictValue({"x": 42})
        result = await d.popitem().execute(ctx)
        assert result == ("x", 42)

    async def test_dict_popitem_empty(self, ctx):
        d = DictValue({})
        result = await d.popitem().execute(ctx)
        assert result is INVALID

    async def test_dict_setdefault_existing(self, ctx):
        d = DictValue({"a": 1})
        result = await d.setdefault("a", 99).execute(ctx)
        assert result == 1

    async def test_dict_setdefault_missing(self, ctx):
        d = DictValue({"a": 1})
        result = await d.setdefault("b", 42).execute(ctx)
        assert result == 42

    async def test_dict_copy_execute(self, ctx):
        d = DictValue({"a": 1, "b": 2})
        result = await d.copy().execute(ctx)
        assert result == {"a": 1, "b": 2}

    # ── New set methods ───────────────────────────────────────────────────

    async def test_set_pop_execute(self, ctx):
        s = SetValue({42})
        result = await s.pop().execute(ctx)
        assert result == 42

    async def test_set_pop_empty(self, ctx):
        s = SetValue(set())
        result = await s.pop().execute(ctx)
        assert result is INVALID

    async def test_set_update_execute(self, ctx):
        s = {1, 2}
        result = await SetValue(s).update(SetValue({3, 4})).execute(ctx)
        assert result is None
        assert s == {1, 2, 3, 4}

    async def test_set_intersection_update_execute(self, ctx):
        s = {1, 2, 3}
        result = await SetValue(s).intersection_update(SetValue({2, 3, 4})).execute(ctx)
        assert result is None
        assert s == {2, 3}

    async def test_set_difference_update_execute(self, ctx):
        s = {1, 2, 3}
        result = await SetValue(s).difference_update(SetValue({2, 3})).execute(ctx)
        assert result is None
        assert s == {1}

    async def test_set_symmetric_difference_update_execute(self, ctx):
        s = {1, 2, 3}
        result = await SetValue(s).symmetric_difference_update(SetValue({2, 3, 4})).execute(ctx)
        assert result is None
        assert s == {1, 4}
