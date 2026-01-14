"""Functional tests for child operations.

Tests container child manipulation operations:
- exists_child(), get_child_type() - child queries
- put_child_primitive(), create_child_container() - child creation
- iter_children(), iter_child_keys() - child enumeration
- delete_child(), clear_children() - child deletion
"""

import pytest

from everyshape.container import (
    ContainerNotFoundError,
    ContainerProtocol,
    ContainerStructure,
    ContainerTypeError,
    clear_children,
    count_children,
    create_child_container,
    create_container,
    delete_child,
    exists_child,
    get_child_type,
    iter_child_keys,
    iter_children,
    node_exists,
    put_child_primitive,
)
from everyshape.container.container_ops import get_child_primitive
from everyshape.container.types import NodeType
from everyshape.storage import TransactionProtocol
from everyshape.typing import EMPTY


# ============================================================================
# CHILD QUERY TESTS
# ============================================================================


def test_exists_child_nonexistent(tx: TransactionProtocol) -> None:
    """Test exists_child returns False for nonexistent child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert not exists_child(("users",), "alice", tx)


def test_exists_child_primitive(tx: TransactionProtocol) -> None:
    """Test exists_child returns True for primitive child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)

    assert exists_child(("users",), "alice", tx)


def test_exists_child_container(tx: TransactionProtocol) -> None:
    """Test exists_child returns True for container child."""
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

    assert exists_child(("users",), "alice", tx)


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
    put_child_primitive(("users",), "name", "Alice", tx)

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


def test_put_child_primitive_basic(tx: TransactionProtocol) -> None:
    """Test putting primitive child."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    put_child_primitive(("users",), "name", "Alice", tx)

    assert exists_child(("users",), "name", tx)
    assert get_child_type(("users",), "name", tx) == NodeType.PRIMITIVE


def test_put_child_primitive_various_types(tx: TransactionProtocol) -> None:
    """Test putting primitive children with various value types."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    put_child_primitive(("data",), "string", "hello", tx)
    put_child_primitive(("data",), "number", 42, tx)
    put_child_primitive(("data",), "float", 3.14, tx)
    put_child_primitive(("data",), "bool", True, tx)
    put_child_primitive(("data",), "none", None, tx)
    put_child_primitive(("data",), "dict", {"key": "value"}, tx)
    put_child_primitive(("data",), "list", [1, 2, 3], tx)

    # Verify all exist
    assert exists_child(("data",), "string", tx)
    assert exists_child(("data",), "number", tx)
    assert exists_child(("data",), "float", tx)
    assert exists_child(("data",), "bool", tx)
    assert exists_child(("data",), "none", tx)
    assert exists_child(("data",), "dict", tx)
    assert exists_child(("data",), "list", tx)


def test_put_child_primitive_update(tx: TransactionProtocol) -> None:
    """Test updating primitive child value."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    put_child_primitive(("users",), "name", "Alice", tx)
    put_child_primitive(("users",), "name", "Bob", tx)

    # Should have been updated
    value = get_child_primitive(("users",), "name", tx)
    assert value == "Bob"


def test_put_child_primitive_over_container_raises(tx: TransactionProtocol) -> None:
    """Test putting primitive over existing container raises error."""
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

    with pytest.raises(ContainerTypeError):
        put_child_primitive(("users",), "alice", "wrong", tx)


def test_put_child_primitive_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test putting child primitive when parent doesn't exist raises error."""
    with pytest.raises(ContainerNotFoundError):
        put_child_primitive(("users",), "alice", "value", tx)


def test_put_child_primitive_parent_not_container_raises(tx: TransactionProtocol) -> None:
    """Test putting child primitive when parent is primitive raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(ContainerTypeError):
        put_child_primitive(("data", "value"), "child", "wrong", tx)


def test_get_child_primitive_basic(tx: TransactionProtocol) -> None:
    """Test getting primitive child value."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "name", "Alice", tx)

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

    with pytest.raises(ContainerTypeError):
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

    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert exists_child(("users",), "alice", tx)
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

    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )
    # Second call should be silent (idempotent)
    create_child_container(
        ("users",),
        "alice",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    # Should still exist
    assert exists_child(("users",), "alice", tx)


def test_create_child_container_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test creating child container when parent doesn't exist raises error."""
    with pytest.raises(ContainerNotFoundError):
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
    put_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(ContainerTypeError):
        create_child_container(
            ("data", "value"),
            "child",
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
            tx,
        )


# ============================================================================
# ITER CHILDREN TESTS
# ============================================================================


def test_iter_child_keys_empty(tx: TransactionProtocol) -> None:
    """Test iterating child keys from empty container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    keys = list(iter_child_keys(("users",), tx))

    assert len(keys) == 0


def test_iter_child_keys_basic(tx: TransactionProtocol) -> None:
    """Test iterating child keys."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    put_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    keys = list(iter_child_keys(("users",), tx))

    assert set(keys) == {"alice", "bob"}


def test_iter_child_keys_mixed(tx: TransactionProtocol) -> None:
    """Test iterating child keys with mixed containers and primitives."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    create_child_container(
        ("users",),
        "posts",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    keys = list(iter_child_keys(("users",), tx))

    assert set(keys) == {"alice", "posts"}


def test_iter_child_keys_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test iterating child keys when parent doesn't exist raises error."""
    with pytest.raises(ContainerNotFoundError):
        list(iter_child_keys(("users",), tx, True))


def test_iter_child_keys_parent_not_container_raises(tx: TransactionProtocol) -> None:
    """Test iterating child keys when parent is primitive raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(ContainerTypeError):
        list(iter_child_keys(("data", "value"), tx, True))


def test_iter_children_empty(tx: TransactionProtocol) -> None:
    """Test iterating children from empty container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    children = list(iter_children(("users",), tx))

    assert len(children) == 0


def test_iter_children_basic(tx: TransactionProtocol) -> None:
    """Test iterating children with node info."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    create_child_container(
        ("users",),
        "posts",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    children = list(iter_children(("users",), tx))

    keys = [k for k, _ in children]
    assert set(keys) == {"alice", "posts"}

    # Verify node info
    for key, info in children:
        if key == "alice":
            assert info.node_type == NodeType.PRIMITIVE
        elif key == "posts":
            assert info.node_type == NodeType.CONTAINER
            assert info.structure == ContainerStructure(2)


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

    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    assert count_children(("users",), tx) == 1

    put_child_primitive(("users",), "bob", {"name": "Bob"}, tx)
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
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)

    delete_child(("users",), "alice", tx)

    assert not exists_child(("users",), "alice", tx)


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
    put_child_primitive(("users", "alice"), "name", "Alice", tx)

    delete_child(("users",), "alice", tx)

    assert not exists_child(("users",), "alice", tx)
    assert not node_exists(("users", "alice", "name"), tx)  # Nested child also deleted


def test_delete_child_nonexistent(tx: TransactionProtocol) -> None:
    """Test deleting nonexistent child is silent (idempotent)."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Should not raise - silent operation
    delete_child(("users",), "alice", tx)


def test_delete_child_parent_not_found_raises(tx: TransactionProtocol) -> None:
    """Test deleting child when parent doesn't exist raises error."""
    with pytest.raises(ContainerNotFoundError):
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
    put_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(ContainerTypeError):
        delete_child(("data", "value"), "child", tx)


# ============================================================================
# CLEAR CHILDREN TESTS
# ============================================================================


def test_clear_children_basic(tx: TransactionProtocol) -> None:
    """Test clearing all children."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    put_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    clear_children(("users",), tx)

    assert count_children(("users",), tx) == 0


def test_clear_children_empty(tx: TransactionProtocol) -> None:
    """Test clearing children from empty container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Should be silent (idempotent)
    clear_children(("users",), tx)

    assert count_children(("users",), tx) == 0


def test_clear_children_mixed(tx: TransactionProtocol) -> None:
    """Test clearing children with mixed containers and primitives."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    create_child_container(
        ("users",),
        "posts",
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
    )

    clear_children(("users",), tx)

    assert count_children(("users",), tx) == 0


def test_clear_children_preserves_container(tx: TransactionProtocol) -> None:
    """Test clearing children preserves the parent container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)

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
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    put_child_primitive(("users",), "bob", {"name": "Bob"}, tx)
    put_child_primitive(("users",), "charlie", {"name": "Charlie"}, tx)

    # Delete one child
    delete_child(("users",), "bob", tx)

    # Verify siblings still exist
    assert exists_child(("users",), "alice", tx)
    assert not exists_child(("users",), "bob", tx)
    assert exists_child(("users",), "charlie", tx)


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
    put_child_primitive(("data",), "key1", "value1", tx)
    put_child_primitive(("data",), "key-with-dash", "value2", tx)
    put_child_primitive(("data",), "key_with_underscore", "value3", tx)

    # Verify all exist
    assert exists_child(("data",), "key1", tx)
    assert exists_child(("data",), "key-with-dash", tx)
    assert exists_child(("data",), "key_with_underscore", tx)


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
    put_child_primitive(("a", "b", "c", "d"), "value", "test", tx)

    assert exists_child(("a", "b", "c", "d"), "value", tx)
    assert get_child_primitive(("a", "b", "c", "d"), "value", tx) == "test"

    # Delete child
    delete_child(("a", "b", "c", "d"), "value", tx)
    assert not exists_child(("a", "b", "c", "d"), "value", tx)


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
    put_child_primitive(("users",), "a", 1, tx)
    create_child_container(
        ("users",),
        "b",
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )
    put_child_primitive(("users",), "c", 3, tx)

    # Iter and verify
    keys = set(iter_child_keys(("users",), tx))
    assert keys == {"a", "b", "c"}

    # Delete one
    delete_child(("users",), "b", tx)

    # Add another
    put_child_primitive(("users",), "d", 4, tx)

    # Final verification
    keys = set(iter_child_keys(("users",), tx))
    assert keys == {"a", "c", "d"}
