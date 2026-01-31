"""Functional tests for ListView."""


def test_list_factory_creates_empty_view(list_factory):
    """Verify list_factory creates an empty ListView."""
    items = list_factory("items")
    assert items is not None
    assert len(items) == 0


def test_list_factory_with_data(list_factory):
    """Verify list_factory can populate initial data."""
    items = list_factory("items", [1, 2, 3, 4, 5])

    data = items.extract()
    assert len(data) == 5
    assert data[0] == 1
    assert data[4] == 5


# ============================================================================
# BASIC OPERATIONS
# ============================================================================


def test_list_append(list_factory):
    """Test appending items."""
    items = list_factory("items")

    items.append(1)
    items.append(2)
    items.append(3)

    assert len(items) == 3
    assert items[0] == 1
    assert items[2] == 3


def test_list_indexing(list_factory):
    """Test index-based access."""
    items = list_factory("items", [10, 20, 30, 40, 50])

    assert items[0] == 10
    assert items[2] == 30
    assert items[4] == 50


def test_list_set_item(list_factory):
    """Test setting items by index."""
    items = list_factory("items", [1, 2, 3])

    items[1] = 99

    assert items[0] == 1
    assert items[1] == 99
    assert items[2] == 3


def test_list_len(list_factory):
    """Test length tracking."""
    items = list_factory("items")

    assert len(items) == 0

    items.append(1)
    assert len(items) == 1

    items.append(2)
    items.append(3)
    assert len(items) == 3


def test_list_iteration(list_factory):
    """Test iterating over list."""
    items = list_factory("items", [1, 2, 3, 4, 5])

    result = []
    for item in items:
        result.append(item)

    assert result == [1, 2, 3, 4, 5]


# ============================================================================
# LIST METHODS
# ============================================================================


def test_list_insert(list_factory):
    """Test insert operation."""
    items = list_factory("items", [1, 3, 4])

    items.insert(1, 2)  # Insert 2 at index 1

    extracted = items.extract()
    assert extracted == [1, 2, 3, 4]


def test_list_pop(list_factory):
    """Test pop operation."""
    items = list_factory("items", [1, 2, 3, 4, 5])

    value = items.pop()
    assert value == 5
    assert len(items) == 4

    value = items.pop(0)
    assert value == 1
    assert len(items) == 3


def test_list_clear(list_factory):
    """Test clear operation."""
    items = list_factory("items", [1, 2, 3, 4, 5])

    items.clear()

    assert len(items) == 0
    assert items.extract() == []


def test_list_contains(list_factory):
    """Test membership checking."""
    items = list_factory("items", [1, 2, 3, 4, 5])

    assert 3 in items
    assert 10 not in items


# ============================================================================
# NESTED DATA
# ============================================================================


def test_list_nested_dicts(list_factory):
    """Test lists containing dictionaries."""
    items = list_factory(
        "items",
        [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ],
    )

    extracted = items.extract()
    assert extracted[0]["name"] == "Alice"
    assert extracted[1]["age"] == 25


def test_list_nested_lists(list_factory):
    """Test nested list structures."""
    items = list_factory(
        "items",
        [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ],
    )

    extracted = items.extract()
    assert extracted[0] == [1, 2, 3]
    assert extracted[2][1] == 8


def test_list_mixed_types(list_factory):
    """Test list with mixed types."""
    items = list_factory(
        "items",
        [
            "string",
            42,
            3.14,
            True,
            {"key": "value"},
            [1, 2, 3],
        ],
    )

    extracted = items.extract()
    assert extracted[0] == "string"
    assert extracted[1] == 42
    assert extracted[4]["key"] == "value"
    assert extracted[5] == [1, 2, 3]


# ============================================================================
# STORE AND EXTRACT
# ============================================================================


def test_list_store_replaces_content(list_factory):
    """Test store() replaces existing content."""
    items = list_factory("items", [1, 2, 3])

    items.store([4, 5, 6, 7])

    assert len(items) == 4
    assert items.extract() == [4, 5, 6, 7]


def test_list_extract_full(list_factory):
    """Test extract() returns full list."""
    items = list_factory("items", [10, 20, 30, 40, 50])

    extracted = items.extract()

    assert extracted == [10, 20, 30, 40, 50]
    assert isinstance(extracted, list)
