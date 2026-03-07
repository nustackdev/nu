"""Functional tests for TupleView."""


def test_tuple_factory_creates_empty_view(tuple_factory):
    """Verify tuple_factory creates an empty TupleView."""
    coords = tuple_factory("coords")
    assert coords is not None
    assert len(coords) == 0


def test_tuple_factory_with_data(tuple_factory):
    """Verify tuple_factory can populate initial data."""
    coords = tuple_factory("coords", (10, 20, 30))

    data = coords.extract()
    assert len(data) == 3
    assert data[0] == 10
    assert data[2] == 30


# ============================================================================
# BASIC OPERATIONS
# ============================================================================


def test_tuple_indexing(tuple_factory):
    """Test index-based access."""
    coords = tuple_factory("coords", (10, 20, 30, 40, 50))

    assert coords[0] == 10
    assert coords[2] == 30
    assert coords[4] == 50


def test_tuple_len(tuple_factory):
    """Test length."""
    empty = tuple_factory("empty", ())
    assert len(empty) == 0

    coords = tuple_factory("coords", (1, 2, 3, 4, 5))
    assert len(coords) == 5


def test_tuple_iteration(tuple_factory):
    """Test iterating over tuple."""
    coords = tuple_factory("coords", (1, 2, 3, 4, 5))

    result = []
    for item in coords:
        result.append(item)

    assert result == [1, 2, 3, 4, 5]


def test_tuple_contains(tuple_factory):
    """Test membership checking."""
    coords = tuple_factory("coords", (10, 20, 30))

    assert 20 in coords
    assert 99 not in coords


# ============================================================================
# NESTED DATA
# ============================================================================


def test_tuple_nested_tuples(tuple_factory):
    """Test nested tuple structures."""
    data = tuple_factory(
        "data",
        (
            (1, 2, 3),
            (4, 5, 6),
            (7, 8, 9),
        ),
    )

    extracted = data.extract()
    assert extracted[0] == (1, 2, 3)
    assert extracted[2][1] == 8


def test_tuple_mixed_types(tuple_factory):
    """Test tuple with mixed types."""
    data = tuple_factory(
        "data",
        (
            "string",
            42,
            3.14,
            True,
        ),
    )

    extracted = data.extract()
    assert extracted[0] == "string"
    assert extracted[1] == 42
    assert extracted[2] == 3.14
    assert extracted[3] is True


# ============================================================================
# STORE AND EXTRACT
# ============================================================================


def test_tuple_store_replaces_content(tuple_factory):
    """Test store() replaces existing content."""
    data = tuple_factory("data", (1, 2, 3))

    data.store((4, 5, 6, 7))

    assert len(data) == 4
    assert data.extract() == (4, 5, 6, 7)


def test_tuple_extract_full(tuple_factory):
    """Test extract() returns full tuple."""
    data = tuple_factory("data", (10, 20, 30, 40, 50))

    extracted = data.extract()

    assert extracted == (10, 20, 30, 40, 50)
    assert isinstance(extracted, tuple)
