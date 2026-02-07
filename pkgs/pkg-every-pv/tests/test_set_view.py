"""Functional tests for SetView."""


def test_set_factory_creates_empty_view(set_factory):
    """Verify set_factory creates an empty SetView."""
    tags = set_factory("tags")
    assert tags is not None
    assert len(tags) == 0


def test_set_factory_with_data(set_factory):
    """Verify set_factory can populate initial data."""
    tags = set_factory("tags", {"python", "rust", "go"})

    data = tags.extract()
    assert len(data) == 3
    assert "python" in data
    assert "rust" in data
    assert "go" in data


# ============================================================================
# BASIC OPERATIONS
# ============================================================================


def test_set_add(set_factory):
    """Test adding elements."""
    tags = set_factory("tags")

    tags.add("python")
    tags.add("rust")
    tags.add("go")

    assert len(tags) == 3
    assert "python" in tags
    assert "rust" in tags


def test_set_add_duplicate(set_factory):
    """Test adding duplicate elements (should be idempotent)."""
    tags = set_factory("tags", {"python"})

    tags.add("python")  # Add again
    tags.add("python")  # And again

    assert len(tags) == 1
    assert "python" in tags


def test_set_contains(set_factory):
    """Test membership checking."""
    tags = set_factory("tags", {"python", "rust", "go"})

    assert "python" in tags
    assert "rust" in tags
    assert "javascript" not in tags


def test_set_len(set_factory):
    """Test length tracking."""
    tags = set_factory("tags")

    assert len(tags) == 0

    tags.add("python")
    assert len(tags) == 1

    tags.add("rust")
    tags.add("go")
    assert len(tags) == 3


def test_set_iteration(set_factory):
    """Test iterating over set."""
    tags = set_factory("tags", {"python", "rust", "go"})

    result = set()
    for tag in tags:
        result.add(tag)

    assert result == {"python", "rust", "go"}


# ============================================================================
# SET METHODS
# ============================================================================


def test_set_remove(set_factory):
    """Test remove operation."""
    tags = set_factory("tags", {"python", "rust", "go"})

    tags.remove("rust")

    assert len(tags) == 2
    assert "python" in tags
    assert "rust" not in tags
    assert "go" in tags


def test_set_discard(set_factory):
    """Test discard operation (doesn't raise if missing)."""
    tags = set_factory("tags", {"python", "rust"})

    tags.discard("rust")  # Exists
    tags.discard("go")  # Doesn't exist (no error)

    assert len(tags) == 1
    assert "python" in tags


def test_set_clear(set_factory):
    """Test clear operation."""
    tags = set_factory("tags", {"python", "rust", "go"})

    tags.clear()

    assert len(tags) == 0
    assert tags.extract() == set()


# ============================================================================
# STORE AND EXTRACT
# ============================================================================


def test_set_store_replaces_content(set_factory):
    """Test store() replaces existing content."""
    tags = set_factory("tags", {"python", "rust"})

    tags.store({"go", "typescript", "java"})

    assert "python" not in tags
    assert "rust" not in tags
    assert tags.extract() == {"go", "typescript", "java"}


def test_set_extract_full(set_factory):
    """Test extract() returns full set."""
    tags = set_factory("tags", {"python", "rust", "go"})

    extracted = tags.extract()

    assert extracted == {"python", "rust", "go"}
    assert isinstance(extracted, set)
