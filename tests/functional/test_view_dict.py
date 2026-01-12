"""Functional tests for DictView operations.

Tests the complete view layer functionality using DictView as the primary test subject.
Covers:
- Basic CRUD operations
- Nested container handling
- Observable subscriptions
- Length tracking
- Extract/store operations
- Navigation
"""

from typing import cast

import pytest

from everyshape.storage import TransactionProtocol
from everyshape.view import (
    is_assignable,
    is_child_observable,
    is_clearable,
    is_containable,
    is_convertible,
    is_deletable,
    is_initializable,
    is_nestable,
    is_observable,
    is_sizeable,
    is_subscriptable,
)
from tests.support.dict_view import DictView


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def view(tx: TransactionProtocol) -> DictView:
    """Create a DictView at root for testing."""
    return DictView.open_root(tx)


# =============================================================================
# PROTOCOL COMPLIANCE TESTS
# =============================================================================


class TestDictViewProtocols:
    """Test that DictView implements expected protocols."""

    def test_implements_subscriptable(self, view: DictView) -> None:
        """Test DictView implements Subscriptable."""
        assert is_subscriptable(view) is True

    def test_implements_assignable(self, view: DictView) -> None:
        """Test DictView implements Assignable."""
        assert is_assignable(view) is True

    def test_implements_containable(self, view: DictView) -> None:
        """Test DictView implements Containable."""
        assert is_containable(view) is True

    def test_implements_sizeable(self, view: DictView) -> None:
        """Test DictView implements Sizeable."""
        assert is_sizeable(view) is True

    def test_implements_deletable(self, view: DictView) -> None:
        """Test DictView implements Deletable."""
        assert is_deletable(view) is True

    def test_implements_clearable(self, view: DictView) -> None:
        """Test DictView implements Clearable."""
        assert is_clearable(view) is True

    def test_implements_convertible(self, view: DictView) -> None:
        """Test DictView implements Convertible."""
        assert is_convertible(view) is True

    def test_implements_initializable(self, view: DictView) -> None:
        """Test DictView implements Initializable."""
        assert is_initializable(view) is True

    def test_implements_nestable(self, view: DictView) -> None:
        """Test DictView implements Nestable."""
        assert is_nestable(view) is True

    def test_implements_observable(self, view: DictView) -> None:
        """Test DictView implements Observable."""
        assert is_observable(view) is True

    def test_implements_child_observable(self, view: DictView) -> None:
        """Test DictView implements ChildObservable."""
        assert is_child_observable(view) is True


# =============================================================================
# BASIC CRUD OPERATIONS
# =============================================================================


class TestDictViewCRUD:
    """Test basic create, read, update, delete operations."""

    def test_setitem_and_getitem_primitive(self, view: DictView) -> None:
        """Test setting and getting primitive values."""
        view["name"] = "Alice"
        assert view["name"] == "Alice"

    def test_setitem_and_getitem_int_key(self, view: DictView) -> None:
        """Test setting and getting with integer key."""
        view[0] = "first"
        view[1] = "second"
        assert view[0] == "first"
        assert view[1] == "second"

    def test_getitem_missing_raises_keyerror(self, view: DictView) -> None:
        """Test getting missing key raises KeyError."""
        with pytest.raises(KeyError):
            _ = view["missing"]

    def test_setitem_overwrites_existing(self, view: DictView) -> None:
        """Test setting existing key overwrites value."""
        view["key"] = "old"
        view["key"] = "new"
        assert view["key"] == "new"

    def test_delitem_existing(self, view: DictView) -> None:
        """Test deleting existing key."""
        view["key"] = "value"
        del view["key"]
        assert "key" not in view

    def test_delitem_missing_raises_keyerror(self, view: DictView) -> None:
        """Test deleting missing key raises KeyError."""
        with pytest.raises(KeyError):
            del view["missing"]

    def test_contains_true(self, view: DictView) -> None:
        """Test __contains__ returns True for existing key."""
        view["key"] = "value"
        assert "key" in view

    def test_contains_false(self, view: DictView) -> None:
        """Test __contains__ returns False for missing key."""
        assert "missing" not in view


# =============================================================================
# LENGTH TRACKING
# =============================================================================


class TestDictViewLength:
    """Test length tracking via metadata."""

    def test_len_empty(self, view: DictView) -> None:
        """Test len() on empty view."""
        assert len(view) == 0

    def test_len_after_single_insert(self, view: DictView) -> None:
        """Test len() after inserting one item."""
        view["key"] = "value"
        assert len(view) == 1

    def test_len_after_multiple_inserts(self, view: DictView) -> None:
        """Test len() after inserting multiple items."""
        view["a"] = 1
        view["b"] = 2
        view["c"] = 3
        assert len(view) == 3

    def test_len_after_overwrite(self, view: DictView) -> None:
        """Test len() is unchanged after overwriting existing key."""
        view["key"] = "old"
        view["key"] = "new"
        assert len(view) == 1

    def test_len_after_delete(self, view: DictView) -> None:
        """Test len() decrements after delete."""
        view["a"] = 1
        view["b"] = 2
        del view["a"]
        assert len(view) == 1

    def test_len_after_clear(self, view: DictView) -> None:
        """Test len() is 0 after clear."""
        view["a"] = 1
        view["b"] = 2
        view.clear()
        assert len(view) == 0


# =============================================================================
# ITERATION METHODS
# =============================================================================


class TestDictViewIteration:
    """Test keys(), values(), items() iteration."""

    def test_keys_empty(self, view: DictView) -> None:
        """Test keys() on empty view."""
        assert list(view.keys()) == []

    def test_keys_with_items(self, view: DictView) -> None:
        """Test keys() returns all keys."""
        view["a"] = 1
        view["b"] = 2
        view["c"] = 3
        keys = list(view.keys())
        assert set(keys) == {"a", "b", "c"}

    def test_values_empty(self, view: DictView) -> None:
        """Test values() on empty view."""
        assert list(view.values()) == []

    def test_values_with_items(self, view: DictView) -> None:
        """Test values() returns all values."""
        view["a"] = 1
        view["b"] = 2
        view["c"] = 3
        values = list(view.values())
        assert set(values) == {1, 2, 3}

    def test_items_empty(self, view: DictView) -> None:
        """Test items() on empty view."""
        assert list(view.items()) == []

    def test_items_with_items(self, view: DictView) -> None:
        """Test items() returns all key-value pairs."""
        view["a"] = 1
        view["b"] = 2
        items = list(view.items())
        assert set(items) == {("a", 1), ("b", 2)}


# =============================================================================
# GET AND POP METHODS
# =============================================================================


class TestDictViewGetPop:
    """Test get() and pop() methods."""

    def test_get_existing(self, view: DictView) -> None:
        """Test get() returns value for existing key."""
        view["key"] = "value"
        assert view.get("key") == "value"

    def test_get_missing_no_default(self, view: DictView) -> None:
        """Test get() returns EMPTY for missing key without default."""
        from everyshape.types import EMPTY

        result = view.get("missing")
        assert result is EMPTY

    def test_get_missing_with_default(self, view: DictView) -> None:
        """Test get() returns default for missing key."""
        assert view.get("missing", "default") == "default"

    def test_pop_existing(self, view: DictView) -> None:
        """Test pop() returns and removes value."""
        view["key"] = "value"
        result = view.pop("key")
        assert result == "value"
        assert "key" not in view

    def test_pop_missing_no_default_raises(self, view: DictView) -> None:
        """Test pop() raises KeyError for missing key without default."""
        with pytest.raises(KeyError):
            view.pop("missing")

    def test_pop_missing_with_default(self, view: DictView) -> None:
        """Test pop() returns default for missing key."""
        result = view.pop("missing", "default")
        assert result == "default"


# =============================================================================
# CLEAR AND UPDATE METHODS
# =============================================================================


class TestDictViewClearUpdate:
    """Test clear() and update() methods."""

    def test_clear_empty(self, view: DictView) -> None:
        """Test clear() on empty view is no-op."""
        view.clear()
        assert len(view) == 0

    def test_clear_removes_all(self, view: DictView) -> None:
        """Test clear() removes all items."""
        view["a"] = 1
        view["b"] = 2
        view["c"] = 3
        view.clear()
        assert len(view) == 0
        assert "a" not in view

    def test_update_from_dict(self, view: DictView) -> None:
        """Test update() from dict."""
        view.update({"a": 1, "b": 2})
        assert view["a"] == 1
        assert view["b"] == 2

    def test_update_from_kwargs(self, view: DictView) -> None:
        """Test update() from kwargs."""
        view.update(a=1, b=2)
        assert view["a"] == 1
        assert view["b"] == 2

    def test_update_merges_existing(self, view: DictView) -> None:
        """Test update() merges with existing items."""
        view["a"] = 1
        view.update({"b": 2, "a": 10})
        assert view["a"] == 10
        assert view["b"] == 2


# =============================================================================
# EXTRACT AND STORE
# =============================================================================


class TestDictViewExtractStore:
    """Test extract() and store() methods."""

    def test_extract_empty(self, view: DictView) -> None:
        """Test extract() on empty view returns empty dict."""
        result = view.extract()
        assert result == {}

    def test_extract_primitives(self, view: DictView) -> None:
        """Test extract() returns dict of primitive values."""
        view["a"] = 1
        view["b"] = "hello"
        view["c"] = 3.14
        result = view.extract()
        assert result == {"a": 1, "b": "hello", "c": 3.14}

    def test_store_replaces_content(self, view: DictView) -> None:
        """Test store() replaces existing content."""
        view["old"] = "value"
        view.store({"new": "value"})
        assert "old" not in view
        assert view["new"] == "value"

    def test_store_roundtrip(self, view: DictView) -> None:
        """Test extract/store roundtrip preserves data."""
        original = {"a": 1, "b": 2, "c": 3}
        view.store(original)
        extracted = view.extract()
        assert extracted == original


# =============================================================================
# NESTED CONTAINERS
# =============================================================================


class TestDictViewNestedContainers:
    """Test nested container handling."""

    def test_set_nested_dict(self, view: DictView) -> None:
        """Test setting nested dict creates child container."""
        view["user"] = {"name": "Alice", "age": 30}
        result = view["user"]
        assert result == {"name": "Alice", "age": 30}

    def test_set_nested_dict_deep(self, view: DictView) -> None:
        """Test setting deeply nested dicts."""
        view["data"] = {"level1": {"level2": {"value": "deep"}}}
        result = cast("dict", view["data"])
        assert result["level1"]["level2"]["value"] == "deep"

    def test_extract_with_nested(self, view: DictView) -> None:
        """Test extract() returns nested dicts."""
        view["user"] = {"name": "Alice", "profile": {"bio": "Developer"}}
        result = view.extract()
        assert result == {"user": {"name": "Alice", "profile": {"bio": "Developer"}}}

    def test_store_with_nested(self, view: DictView) -> None:
        """Test store() handles nested dicts."""
        data = {
            "users": {
                "alice": {"name": "Alice"},
                "bob": {"name": "Bob"},
            }
        }
        view.store(data)
        assert cast("dict", view["users"])["alice"]["name"] == "Alice"
        assert cast("dict", view["users"])["bob"]["name"] == "Bob"


# =============================================================================
# CHILD NAVIGATION
# =============================================================================


class TestDictViewNavigation:
    """Test child navigation with open_child()."""

    def test_open_child_existing(self, view: DictView) -> None:
        """Test navigating to existing child container."""
        view["users"] = {"alice": {"name": "Alice"}}
        users = view.open_child("users", DictView)
        assert "alice" in users
        assert cast("dict", users["alice"])["name"] == "Alice"

    def test_open_child_modify(self, view: DictView) -> None:
        """Test modifying through child view affects parent."""
        view["users"] = {}
        users = view.open_child("users", DictView)
        users["bob"] = {"name": "Bob"}

        # Verify through parent view
        assert cast("dict", view["users"])["bob"]["name"] == "Bob"


# =============================================================================
# OBSERVABLE SUBSCRIPTIONS
# =============================================================================


class TestDictViewObservable:
    """Test observable subscription functionality.

    Note: Notifications are sent on transaction commit, not during writes.
    These tests verify subscription creation and management, not the notification
    timing which is tested in integration tests with explicit commits.
    """

    def test_on_change_creates_subscription(self, view: DictView) -> None:
        """Test on_change() creates a valid subscription."""
        sub = view.on_change()
        assert sub is not None
        assert not sub.is_closed
        sub.close()
        assert sub.is_closed

    def test_on_child_change_creates_subscription(self, view: DictView) -> None:
        """Test on_child_change() creates a valid subscription."""
        view["users"] = {}
        sub = view.on_child_change("users")
        assert sub is not None
        assert not sub.is_closed
        sub.close()
        assert sub.is_closed

    def test_subscription_bind_and_unbind(self, view: DictView) -> None:
        """Test binding and unbinding callbacks to subscription."""
        changes: list = []

        def callback(key: tuple) -> None:
            changes.append(key)

        sub = view.on_change()
        sub.bind(callback)

        # Should be bound
        assert callback in sub.receivers

        sub.unbind(callback)
        assert callback not in sub.receivers

        sub.close()

    def test_subscription_close_stops_notifications(self, view: DictView) -> None:
        """Test closing subscription marks it as closed."""
        sub = view.on_change()
        assert not sub.is_closed

        sub.close()
        assert sub.is_closed

    def test_on_children_change_creates_subscription(self, view: DictView) -> None:
        """Test on_children_change() creates a valid subscription."""
        sub = view.on_children_change()
        assert sub is not None
        assert not sub.is_closed
        sub.close()
        assert sub.is_closed


# =============================================================================
# EDGE CASES
# =============================================================================


class TestDictViewEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_key(self, view: DictView) -> None:
        """Test empty string as key."""
        view[""] = "empty key"
        assert view[""] == "empty key"

    def test_none_value(self, view: DictView) -> None:
        """Test None as value."""
        view["key"] = None
        assert view["key"] is None

    def test_zero_value(self, view: DictView) -> None:
        """Test 0 as value."""
        view["key"] = 0
        assert view["key"] == 0

    def test_false_value(self, view: DictView) -> None:
        """Test False as value."""
        view["key"] = False
        assert view["key"] is False

    def test_empty_string_value(self, view: DictView) -> None:
        """Test empty string as value."""
        view["key"] = ""
        assert view["key"] == ""

    def test_unicode_key(self, view: DictView) -> None:
        """Test unicode string as key."""
        view["こんにちは"] = "hello"
        assert view["こんにちは"] == "hello"

    def test_unicode_value(self, view: DictView) -> None:
        """Test unicode string as value."""
        view["greeting"] = "こんにちは"
        assert view["greeting"] == "こんにちは"

    def test_large_number_value(self, view: DictView) -> None:
        """Test large number as value."""
        big_num = 10**100
        view["big"] = big_num
        assert view["big"] == big_num

    def test_float_value(self, view: DictView) -> None:
        """Test float as value."""
        view["pi"] = 3.14159265358979
        assert view["pi"] == 3.14159265358979

    def test_negative_int_key(self, view: DictView) -> None:
        """Test negative integer as key."""
        view[-1] = "negative"
        assert view[-1] == "negative"


# =============================================================================
# INTEGRATION TEST
# =============================================================================


class TestDictViewIntegration:
    """Integration tests combining multiple operations."""

    def test_complex_workflow(self, view: DictView) -> None:
        """Test complex workflow with multiple operations."""
        # Store initial data
        view.store(
            {
                "users": {
                    "alice": {"name": "Alice", "age": 30},
                    "bob": {"name": "Bob", "age": 25},
                },
                "settings": {"theme": "dark"},
            }
        )

        # Navigate and modify
        users = view.open_child("users", DictView)
        users["charlie"] = {"name": "Charlie", "age": 35}

        # Delete
        del users["bob"]

        # Verify final state
        extracted = view.extract()
        assert "alice" in cast("dict", extracted["users"])
        assert "charlie" in cast("dict", extracted["users"])
        assert "bob" not in cast("dict", extracted["users"])
        assert cast("dict", extracted["settings"])["theme"] == "dark"

    def test_nested_modification_persistence(self, view: DictView) -> None:
        """Test that nested modifications persist correctly."""
        view["level1"] = {"level2": {"level3": {"value": "original"}}}

        # Navigate deep
        level1 = view.open_child("level1", DictView)
        level2 = level1.open_child("level2", DictView)
        level3 = level2.open_child("level3", DictView)

        # Modify at deepest level
        level3["value"] = "modified"
        level3["new"] = "added"

        # Verify from root
        result = view.extract()
        assert cast("dict", result["level1"])["level2"]["level3"]["value"] == "modified"
        assert cast("dict", result["level1"])["level2"]["level3"]["new"] == "added"
