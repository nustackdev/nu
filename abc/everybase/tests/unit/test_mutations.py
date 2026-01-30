"""Tests for collection mutation commands and capabilities.

Tests that:
1. Mutation command morphisms (cmd_*) apply correctly
2. Mutable collection capabilities wire through to types
3. Type bases (ListType, DictType, SetType) expose mutation methods
"""

import pytest

from everyabc import Context
from everybase import (
    AnyValue,
    DictValue,
    ListValue,
    SetValue,
)
from everybase.morphisms import (
    AddCmd,
    AppendCmd,
    ClearCmd,
    DeleteItemCmd,
    DiscardCmd,
    InsertCmd,
    PopCmd,
    RemoveCmd,
    SetItemCmd,
    UpdateCmd,
)


# =============================================================================
# CONTEXT FIXTURE
# =============================================================================


@pytest.fixture()
def ctx():
    """Minimal execution context."""
    return Context()


# =============================================================================
# SEQUENCE MUTATION COMMANDS
# =============================================================================


class TestAppendCmd:
    """AppendCmd morphism tests."""

    async def test_execute_appends(self, ctx):
        cmd = AppendCmd[int](ListValue([1, 2, 3]), 4)
        result = await cmd.execute(ctx)
        assert result == [1, 2, 3, 4]

    async def test_execute_appends_to_empty(self, ctx):
        cmd = AppendCmd[int](ListValue([]), 1)
        result = await cmd.execute(ctx)
        assert result == [1]


class TestInsertCmd:
    """InsertCmd morphism tests."""

    async def test_execute_inserts_at_index(self, ctx):
        cmd = InsertCmd[int](ListValue([1, 3]), 1, 2)
        result = await cmd.execute(ctx)
        assert result == [1, 2, 3]

    async def test_execute_inserts_at_zero(self, ctx):
        cmd = InsertCmd[str](ListValue(["b", "c"]), 0, "a")
        result = await cmd.execute(ctx)
        assert result == ["a", "b", "c"]


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


# =============================================================================
# MAPPING MUTATION COMMANDS
# =============================================================================


class TestSetItemCmd:
    """SetItemCmd morphism tests."""

    async def test_execute_sets_key(self, ctx):
        cmd = SetItemCmd[str, int](DictValue({"a": 1}), "b", 2)
        result = await cmd.execute(ctx)
        assert result == 2

    async def test_execute_overwrites_key(self, ctx):
        cmd = SetItemCmd[str, int](DictValue({"a": 1}), "a", 99)
        result = await cmd.execute(ctx)
        assert result == 99


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
        assert result == {"a": 1, "b": 2}


# =============================================================================
# SET MUTATION COMMANDS
# =============================================================================


class TestAddCmd:
    """AddCmd morphism tests."""

    async def test_execute_adds_element(self, ctx):
        cmd = AddCmd[int](SetValue({1, 2}), 3)
        result = await cmd.execute(ctx)
        assert result == {1, 2, 3}

    async def test_execute_add_existing(self, ctx):
        cmd = AddCmd[int](SetValue({1, 2}), 2)
        result = await cmd.execute(ctx)
        assert result == {1, 2}


class TestRemoveCmd:
    """RemoveCmd morphism tests."""

    async def test_execute_removes_element(self, ctx):
        cmd = RemoveCmd[int](SetValue({1, 2, 3}), 2)
        result = await cmd.execute(ctx)
        assert result == {1, 3}


class TestDiscardCmd:
    """DiscardCmd morphism tests."""

    async def test_execute_discards_element(self, ctx):
        cmd = DiscardCmd[int](SetValue({1, 2, 3}), 2)
        result = await cmd.execute(ctx)
        assert result == {1, 3}

    async def test_execute_discards_missing(self, ctx):
        cmd = DiscardCmd[int](SetValue({1, 2}), 99)
        result = await cmd.execute(ctx)
        assert result == {1, 2}


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

    def test_append_returns_list_value(self):
        lst = ListValue([1, 2, 3])
        result = lst.append(4)
        assert isinstance(result, ListValue)

    def test_insert_returns_list_value(self):
        lst = ListValue([1, 3])
        result = lst.insert(1, 2)
        assert isinstance(result, ListValue)

    def test_pop_returns_any_value(self):
        lst = ListValue([1, 2, 3])
        result = lst.pop()
        assert isinstance(result, AnyValue)

    def test_clear_returns_value(self):
        lst = ListValue([1, 2, 3])
        result = lst.clear()
        assert isinstance(result, AnyValue)


class TestDictTypeMutations:
    """DictType exposes mutation methods via MutableMappingBase."""

    def test_set_returns_any_value(self):
        d = DictValue({"a": 1})
        result = d.set_("b", 2)
        assert isinstance(result, AnyValue)

    def test_delete_returns_any_value(self):
        d = DictValue({"a": 1})
        result = d.delete("a")
        assert isinstance(result, AnyValue)

    def test_update_returns_any_value(self):
        d = DictValue({"a": 1})
        result = d.update_({"b": 2})
        assert isinstance(result, AnyValue)

    def test_clear_returns_value(self):
        d = DictValue({"a": 1})
        result = d.clear()
        assert isinstance(result, AnyValue)


class TestSetTypeMutations:
    """SetType exposes mutation methods via MutableSetBase."""

    def test_add_returns_set_value(self):
        s = SetValue({1, 2})
        result = s.add(3)
        assert isinstance(result, SetValue)

    def test_remove_returns_set_value(self):
        s = SetValue({1, 2, 3})
        result = s.remove(2)
        assert isinstance(result, SetValue)

    def test_discard_returns_set_value(self):
        s = SetValue({1, 2, 3})
        result = s.discard(2)
        assert isinstance(result, SetValue)

    def test_clear_returns_value(self):
        s = SetValue({1, 2, 3})
        result = s.clear()
        assert isinstance(result, AnyValue)


# =============================================================================
# EXECUTION INTEGRATION TESTS
# =============================================================================


class TestMutationExecution:
    """Test that mutation commands execute correctly end-to-end."""

    async def test_list_append_execute(self, ctx):
        lst = ListValue([1, 2])
        result = await lst.append(3).execute(ctx)
        assert result == [1, 2, 3]

    async def test_list_insert_execute(self, ctx):
        lst = ListValue([1, 3])
        result = await lst.insert(1, 2).execute(ctx)
        assert result == [1, 2, 3]

    async def test_list_pop_execute(self, ctx):
        lst = ListValue([1, 2, 3])
        result = await lst.pop().execute(ctx)
        assert result == 3

    async def test_dict_set_execute(self, ctx):
        d = DictValue({"a": 1})
        result = await d.set_("b", 2).execute(ctx)
        assert result == 2

    async def test_dict_delete_execute(self, ctx):
        d = DictValue({"a": 1, "b": 2})
        result = await d.delete("a").execute(ctx)
        assert result is None

    async def test_dict_update_execute(self, ctx):
        d = DictValue({"a": 1})
        result = await d.update_({"b": 2}).execute(ctx)
        assert result == {"a": 1, "b": 2}

    async def test_set_add_execute(self, ctx):
        s = SetValue({1, 2})
        result = await s.add(3).execute(ctx)
        assert result == {1, 2, 3}

    async def test_set_remove_execute(self, ctx):
        s = SetValue({1, 2, 3})
        result = await s.remove(2).execute(ctx)
        assert result == {1, 3}

    async def test_set_discard_execute(self, ctx):
        s = SetValue({1, 2, 3})
        result = await s.discard(99).execute(ctx)
        assert result == {1, 2, 3}

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
