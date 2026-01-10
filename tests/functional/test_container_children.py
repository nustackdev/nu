"""Functional tests for child operations.

Tests container child manipulation operations:
- has_child(), get_child_type() - child queries
- set_child_primitive(), create_child_container() - child creation
- list_children(), list_child_keys() - child enumeration
- delete_child(), clear_children() - child deletion
"""

import pytest

from everyshape.container import (
    ContainerProtocol,
    ContainerStructure,
    PathNotFoundError,
    PathTypeError,
    clear_children,
    count_children,
    create_child_container,
    create_container,
    delete_child,
    get_child_type,
    has_child,
    list_child_keys,
    list_children,
    node_exists,
    set_child_primitive,
)
from everyshape.container.container_ops import get_child_primitive
from everyshape.container.types import NodeType
from everyshape.storage import TransactionProtocol
from everyshape.types import EMPTY


# ============================================================================
# CHILD QUERY TESTS
# ============================================================================


def test_has_child_nonexistent(tx: TransactionProtocol) -> None:
    """Test has_child returns False for nonexistent child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert not has_child(("users",), "alice", tx)


def test_has_child_primitive(tx: TransactionProtocol) -> None:
    """Test has_child returns True for primitive child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)

    assert has_child(("users",), "alice", tx)


def test_has_child_container(tx: TransactionProtocol) -> None:
    """Test has_child returns True for container child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert has_child(("users",), "alice", tx)


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_has_child_parent_not_container_raises(tx: TransactionProtocol) -> None:
    """Test has_child raises when parent is not a container."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(PathTypeError):
        has_child(("data", "value"), "child", tx)


def test_get_child_type_nonexistent(tx: TransactionProtocol) -> None:
    """Test get_child_type returns NOT_FOUND for nonexistent child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert get_child_type(("users",), "alice", tx) == NodeType.NOT_FOUND


def test_get_child_type_primitive(tx: TransactionProtocol) -> None:
    """Test get_child_type returns PRIMITIVE for primitive child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "name", "Alice", tx)

    assert get_child_type(("users",), "name", tx) == NodeType.PRIMITIVE


def test_get_child_type_container(tx: TransactionProtocol) -> None:
    """Test get_child_type returns CONTAINER for container child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert get_child_type(("users",), "alice", tx) == NodeType.CONTAINER


# ============================================================================
# PRIMITIVE CHILD TESTS
# ============================================================================


def test_set_child_primitive_basic(tx: TransactionProtocol) -> None:
    """Test setting primitive child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    set_child_primitive(("users",), "name", "Alice", tx)

    assert has_child(("users",), "name", tx)
    assert get_child_type(("users",), "name", tx) == NodeType.PRIMITIVE


def test_set_child_primitive_various_types(tx: TransactionProtocol) -> None:
    """Test setting primitive children with various value types."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    set_child_primitive(("data",), "string", "hello", tx)
    set_child_primitive(("data",), "number", 42, tx)
    set_child_primitive(("data",), "float", 3.14, tx)
    set_child_primitive(("data",), "bool", True, tx)
    set_child_primitive(("data",), "none", None, tx)
    set_child_primitive(("data",), "dict", {"key": "value"}, tx)
    set_child_primitive(("data",), "list", [1, 2, 3], tx)

    # Verify all exist
    assert has_child(("data",), "string", tx)
    assert has_child(("data",), "number", tx)
    assert has_child(("data",), "float", tx)
    assert has_child(("data",), "bool", tx)
    assert has_child(("data",), "none", tx)
    assert has_child(("data",), "dict", tx)
    assert has_child(("data",), "list", tx)


def test_set_child_primitive_update(tx: TransactionProtocol) -> None:
    """Test updating primitive child value."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    set_child_primitive(("users",), "name", "Alice", tx)
    set_child_primitive(("users",), "name", "Bob", tx)

    # Should have been updated
    value = get_child_primitive(("users",), "name", tx)
    assert value == "Bob"


def test_set_child_primitive_over_container_raises(tx: TransactionProtocol) -> None:
    """Test setting primitive over existing container raises error."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    with pytest.raises(PathTypeError):
        set_child_primitive(("users",), "alice", "wrong", tx)


def test_set_child_primitive_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test setting child primitive when parent doesn't exist raises error."""
    with pytest.raises(PathNotFoundError):
        set_child_primitive(("users",), "alice", "value", tx)


def test_set_child_primitive_parent_not_container_raises(tx: TransactionProtocol) -> None:
    """Test setting child primitive when parent is primitive raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(PathTypeError):
        set_child_primitive(("data", "value"), "child", "wrong", tx)


def test_get_child_primitive_basic(tx: TransactionProtocol) -> None:
    """Test getting primitive child value."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "name", "Alice", tx)

    value = get_child_primitive(("users",), "name", tx)

    assert value == "Alice"


def test_get_child_primitive_nonexistent(tx: TransactionProtocol) -> None:
    """Test getting nonexistent child returns EMPTY."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    value = get_child_primitive(("users",), "name", tx)

    assert value is EMPTY


def test_get_child_primitive_container_raises(tx: TransactionProtocol) -> None:
    """Test getting container as primitive raises error."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    with pytest.raises(PathTypeError):
        get_child_primitive(("users",), "alice", tx)


# ============================================================================
# CONTAINER CHILD TESTS
# ============================================================================


def test_create_child_container_basic(tx: TransactionProtocol) -> None:
    """Test creating child container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    created = create_child_container(
        ("users",),
        "alice",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert created is True
    assert has_child(("users",), "alice", tx)
    assert get_child_type(("users",), "alice", tx) == NodeType.CONTAINER


def test_create_child_container_idempotent(tx: TransactionProtocol) -> None:
    """Test creating child container twice with same type is idempotent."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    created1 = create_child_container(
        ("users",),
        "alice",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )
    created2 = create_child_container(
        ("users",),
        "alice",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert created1 is True
    assert created2 is False  # Already exists


def test_create_child_container_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test creating child container when parent doesn't exist raises error."""
    with pytest.raises(PathNotFoundError):
        create_child_container(
            ("users",),
            "alice",
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
            tx,
        )


def test_create_child_container_parent_not_container_raises(tx: TransactionProtocol) -> None:
    """Test creating child container when parent is primitive raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(PathTypeError):
        create_child_container(
            ("data", "value"),
            "child",
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
            tx,
        )


# ============================================================================
# LIST CHILDREN TESTS
# Note: These tests require scan operations which MemoryStorage doesn't support
# ============================================================================


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_list_child_keys_empty(tx: TransactionProtocol) -> None:
    """Test listing child keys from empty container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    keys = list(list_child_keys(("users",), tx))

    assert len(keys) == 0


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_list_child_keys_basic(tx: TransactionProtocol) -> None:
    """Test listing child keys."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    set_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    keys = list(list_child_keys(("users",), tx))

    assert set(keys) == {"alice", "bob"}


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_list_child_keys_mixed(tx: TransactionProtocol) -> None:
    """Test listing child keys with mixed containers and primitives."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    create_child_container(
        ("users",),
        "posts",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    keys = list(list_child_keys(("users",), tx))

    assert set(keys) == {"alice", "posts"}


def test_list_child_keys_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test listing child keys when parent doesn't exist raises error."""
    with pytest.raises(PathNotFoundError):
        list(list_child_keys(("users",), tx))


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_list_child_keys_parent_not_container_raises(tx: TransactionProtocol) -> None:
    """Test listing child keys when parent is primitive raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(PathTypeError):
        list(list_child_keys(("data", "value"), tx))


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_list_children_empty(tx: TransactionProtocol) -> None:
    """Test listing children from empty container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    children = list(list_children(("users",), tx))

    assert len(children) == 0


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_list_children_basic(tx: TransactionProtocol) -> None:
    """Test listing children with node info."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    create_child_container(
        ("users",),
        "posts",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    children = list(list_children(("users",), tx))

    keys = [k for k, _ in children]
    assert set(keys) == {"alice", "posts"}

    # Verify node info
    for key, info in children:
        if key == "alice":
            assert info.node_type == NodeType.PRIMITIVE
        elif key == "posts":
            assert info.node_type == NodeType.CONTAINER
            assert info.structure == ContainerStructure(2)


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_count_children_basic(tx: TransactionProtocol) -> None:
    """Test counting children."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert count_children(("users",), tx) == 0

    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    assert count_children(("users",), tx) == 1

    set_child_primitive(("users",), "bob", {"name": "Bob"}, tx)
    assert count_children(("users",), tx) == 2


# ============================================================================
# DELETE CHILD TESTS
# ============================================================================


def test_delete_child_primitive(tx: TransactionProtocol) -> None:
    """Test deleting primitive child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)

    deleted = delete_child(("users",), "alice", tx)

    assert deleted is True
    assert not has_child(("users",), "alice", tx)


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_delete_child_container(tx: TransactionProtocol) -> None:
    """Test deleting container child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )
    set_child_primitive(("users", "alice"), "name", "Alice", tx)

    deleted = delete_child(("users",), "alice", tx)

    assert deleted is True
    assert not has_child(("users",), "alice", tx)
    assert not node_exists(("users", "alice", "name"), tx)  # Nested child also deleted


def test_delete_child_nonexistent(tx: TransactionProtocol) -> None:
    """Test deleting nonexistent child returns False."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    deleted = delete_child(("users",), "alice", tx)

    assert deleted is False


def test_delete_child_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test deleting child when parent doesn't exist raises error."""
    with pytest.raises(PathNotFoundError):
        delete_child(("users",), "alice", tx)


def test_delete_child_parent_not_container_raises(tx: TransactionProtocol) -> None:
    """Test deleting child when parent is primitive raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(PathTypeError):
        delete_child(("data", "value"), "child", tx)


# ============================================================================
# CLEAR CHILDREN TESTS
# Note: These tests require scan operations which MemoryStorage doesn't support
# ============================================================================


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_clear_children_basic(tx: TransactionProtocol) -> None:
    """Test clearing all children."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    set_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    count = clear_children(("users",), tx)

    assert count == 2
    assert count_children(("users",), tx) == 0


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_clear_children_empty(tx: TransactionProtocol) -> None:
    """Test clearing children from empty container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    count = clear_children(("users",), tx)

    assert count == 0


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_clear_children_mixed(tx: TransactionProtocol) -> None:
    """Test clearing children with mixed containers and primitives."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    create_child_container(
        ("users",),
        "posts",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    count = clear_children(("users",), tx)

    assert count == 2
    assert count_children(("users",), tx) == 0


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_clear_children_preserves_container(tx: TransactionProtocol) -> None:
    """Test clearing children preserves the parent container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)

    clear_children(("users",), tx)

    # Container should still exist
    assert node_exists(("users",), tx)
    assert get_child_type(("users",), "alice", tx) == NodeType.NOT_FOUND


# ============================================================================
# EDGE CASES AND INTEGRATION
# ============================================================================


def test_child_operations_preserve_siblings(tx: TransactionProtocol) -> None:
    """Test child operations preserve sibling children."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    set_child_primitive(("users",), "bob", {"name": "Bob"}, tx)
    set_child_primitive(("users",), "charlie", {"name": "Charlie"}, tx)

    # Delete one child
    delete_child(("users",), "bob", tx)

    # Verify siblings still exist
    assert has_child(("users",), "alice", tx)
    assert not has_child(("users",), "bob", tx)
    assert has_child(("users",), "charlie", tx)


def test_child_operations_various_key_types(tx: TransactionProtocol) -> None:
    """Test child operations with various key segment types."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # String keys
    set_child_primitive(("data",), "key1", "value1", tx)
    set_child_primitive(("data",), "key-with-dash", "value2", tx)
    set_child_primitive(("data",), "key_with_underscore", "value3", tx)

    # Verify all exist
    assert has_child(("data",), "key1", tx)
    assert has_child(("data",), "key-with-dash", tx)
    assert has_child(("data",), "key_with_underscore", tx)


def test_deep_nesting_child_operations(tx: TransactionProtocol) -> None:
    """Test child operations work correctly with deep nesting."""
    create_container(
        ("a", "b", "c", "d"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )

    # Add child to deeply nested container
    set_child_primitive(("a", "b", "c", "d"), "value", "test", tx)

    assert has_child(("a", "b", "c", "d"), "value", tx)
    assert get_child_primitive(("a", "b", "c", "d"), "value", tx) == "test"

    # Delete child
    deleted = delete_child(("a", "b", "c", "d"), "value", tx)
    assert deleted is True
    assert not has_child(("a", "b", "c", "d"), "value", tx)


@pytest.mark.skip(reason="Requires scan operation not implemented in MemoryStorage")
def test_child_operations_interleaved(tx: TransactionProtocol) -> None:
    """Test interleaving different child operations works correctly."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Add children
    set_child_primitive(("users",), "a", 1, tx)
    create_child_container(
        ("users",),
        "b",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )
    set_child_primitive(("users",), "c", 3, tx)

    # List and verify
    keys = set(list_child_keys(("users",), tx))
    assert keys == {"a", "b", "c"}

    # Delete one
    delete_child(("users",), "b", tx)

    # Add another
    set_child_primitive(("users",), "d", 4, tx)

    # Final verification
    keys = set(list_child_keys(("users",), tx))
    assert keys == {"a", "c", "d"}
