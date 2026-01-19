"""Functional tests for container lifecycle operations.

Tests container creation, deletion, and descendant operations:
- create_container() - creating containers with parent validation
- delete_container() - deleting containers
- delete_descendants() - recursive deletion
- create_parents() - automatic parent creation
"""

import pytest

from everykv.container import (
    ContainerExistsError,
    ContainerProtocol,
    ContainerStructure,
    ContainerTypeError,
    create_container,
    create_parents,
    delete_container,
    delete_descendants,
    get_node_info,
    get_node_type,
    node_exists,
    put_child_primitive,
)
from everykv.container.types import NodeType
from everykv.storage import TransactionProtocol


# ============================================================================
# CONTAINER CREATION TESTS
# ============================================================================


def test_create_container_basic(tx: TransactionProtocol) -> None:
    """Test basic container creation without parent validation."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert node_exists(("users",), tx)
    assert get_node_type(("users",), tx) == NodeType.CONTAINER

    info = get_node_info(("users",), tx)
    assert info.structure == ContainerStructure(1)
    assert info.protocol == ContainerProtocol.MUTABLE


def test_create_container_idempotent_compatible(tx: TransactionProtocol) -> None:
    """Test creating container twice with same type is idempotent."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    # Second call should be silent (idempotent)
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Should still exist with same type
    assert node_exists(("users",), tx)
    info = get_node_info(("users",), tx)
    assert info.structure == ContainerStructure(1)


def test_create_container_incompatible_type_raises(tx: TransactionProtocol) -> None:
    """Test creating container with incompatible type raises error."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    with pytest.raises(ContainerExistsError):
        create_container(
            ("users",),
            ContainerStructure(2),  # Different structure
            ContainerProtocol.MUTABLE,
            tx,
            ensure_healthy_parents=False,
        )


def test_create_container_over_primitive_raises(tx: TransactionProtocol) -> None:
    """Test creating container where primitive exists raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(ContainerTypeError):
        create_container(
            ("data", "value"),
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
            tx,
            ensure_healthy_parents=False,
        )


def test_create_container_various_protocols(tx: TransactionProtocol) -> None:
    """Test creating containers with various protocol combinations."""
    create_container(
        ("c1",),
        ContainerStructure(1),
        ContainerProtocol.NONE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("c2",),
        ContainerStructure(2),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("c3",),
        ContainerStructure(3),
        ContainerProtocol.MUTABLE | ContainerProtocol.SIZED,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("c4",),
        ContainerStructure(4),
        ContainerProtocol.MUTABLE | ContainerProtocol.SIZED | ContainerProtocol.INDEXED,
        tx,
        ensure_healthy_parents=False,
    )

    # Verify all created with correct protocols
    assert get_node_info(("c1",), tx).protocol == ContainerProtocol.NONE
    assert get_node_info(("c2",), tx).protocol == ContainerProtocol.MUTABLE
    assert (
        get_node_info(("c3",), tx).protocol == ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
    )
    assert (
        get_node_info(("c4",), tx).protocol
        == ContainerProtocol.MUTABLE | ContainerProtocol.SIZED | ContainerProtocol.INDEXED
    )


# ============================================================================
# PARENT VALIDATION TESTS
# ============================================================================


def test_create_container_with_ensure_healthy_parents(tx: TransactionProtocol) -> None:
    """Test creating container with automatic parent creation."""
    create_container(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )

    # Verify target exists
    assert node_exists(("a", "b", "c"), tx)

    # Verify parents were created
    assert node_exists(("a",), tx)
    assert node_exists(("a", "b"), tx)
    assert get_node_type(("a",), tx) == NodeType.CONTAINER
    assert get_node_type(("a", "b"), tx) == NodeType.CONTAINER


def test_create_container_without_ensure_healthy_parents_missing(
    tx: TransactionProtocol,
) -> None:
    """Test creating container without parent validation allows missing parents."""
    # When ensure_healthy_parents=False, creation is allowed even without parents
    create_container(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert node_exists(("a", "b", "c"), tx)
    # Parents don't exist
    assert not node_exists(("a",), tx)
    assert not node_exists(("a", "b"), tx)


def test_create_container_malformed_parent_raises(tx: TransactionProtocol) -> None:
    """Test creating container with malformed parent raises error."""
    # Create a primitive where parent should be
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("a",), "b", "wrong", tx)

    with pytest.raises(ContainerTypeError):  # ContainerParentMalformedError is subclass
        create_container(
            ("a", "b", "c"),
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
            tx,
            ensure_healthy_parents=True,
        )


def test_create_container_with_custom_parent_defaults(tx: TransactionProtocol) -> None:
    """Test creating container with custom parent structure and protocol."""
    create_container(
        ("a", "b", "c"),
        ContainerStructure(5),
        ContainerProtocol.MUTABLE | ContainerProtocol.SIZED,
        tx,
        ensure_healthy_parents=True,
        default_parent_structure=ContainerStructure(10),
        default_parent_protocol=ContainerProtocol.MUTABLE | ContainerProtocol.INDEXED,
    )

    # Target should have its specified type
    target_info = get_node_info(("a", "b", "c"), tx)
    assert target_info.structure == ContainerStructure(5)
    assert target_info.protocol == ContainerProtocol.MUTABLE | ContainerProtocol.SIZED

    # Parents should have default type
    parent_a_info = get_node_info(("a",), tx)
    assert parent_a_info.structure == ContainerStructure(10)
    assert parent_a_info.protocol == ContainerProtocol.MUTABLE | ContainerProtocol.INDEXED

    parent_b_info = get_node_info(("a", "b"), tx)
    assert parent_b_info.structure == ContainerStructure(10)
    assert parent_b_info.protocol == ContainerProtocol.MUTABLE | ContainerProtocol.INDEXED


# ============================================================================
# CREATE PARENTS TESTS
# ============================================================================


def test_create_parents_all_missing(tx: TransactionProtocol) -> None:
    """Test create_parents creates all missing parents."""
    create_parents(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    # Verify parents exist
    assert node_exists(("a",), tx)
    assert node_exists(("a", "b"), tx)


def test_create_parents_partially_missing(tx: TransactionProtocol) -> None:
    """Test create_parents only creates missing parents."""
    # Create first parent manually
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    create_parents(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    # Both should exist now
    assert node_exists(("a",), tx)
    assert node_exists(("a", "b"), tx)


def test_create_parents_all_exist(tx: TransactionProtocol) -> None:
    """Test create_parents is silent when all parents exist."""
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("a", "b"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Should not raise - silent operation
    create_parents(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )


def test_create_parents_malformed_raises(tx: TransactionProtocol) -> None:
    """Test create_parents raises when parent is malformed."""
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("a",), "b", "wrong", tx)

    with pytest.raises(ContainerTypeError):  # ContainerParentMalformedError is subclass
        create_parents(
            ("a", "b", "c"),
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
            tx,
        )


def test_create_parents_root_level(tx: TransactionProtocol) -> None:
    """Test create_parents for root-level site is silent."""
    # Should not raise - silent operation (no parents to create)
    create_parents(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )


# ============================================================================
# CONTAINER DELETION TESTS
# ============================================================================


def test_delete_container_basic(tx: TransactionProtocol) -> None:
    """Test basic container deletion."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    delete_container(("users",), tx)

    assert not node_exists(("users",), tx)


def test_delete_container_nonexistent(tx: TransactionProtocol) -> None:
    """Test deleting nonexistent container is silent (idempotent)."""
    # Should not raise - silent operation
    delete_container(("users",), tx)


def test_delete_container_primitive_raises(tx: TransactionProtocol) -> None:
    """Test deleting primitive as container raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(ContainerTypeError):
        delete_container(("data", "value"), tx)


def test_delete_container_with_children(tx: TransactionProtocol) -> None:
    """Test deleting container with children deletes entire descendants."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    put_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    delete_container(("users",), tx)

    assert not node_exists(("users",), tx)
    assert not node_exists(("users", "alice"), tx)
    assert not node_exists(("users", "bob"), tx)


def test_delete_container_deep_hierarchy(tx: TransactionProtocol) -> None:
    """Test deleting container with deep nested children."""
    create_container(
        ("a", "b", "c", "d"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )
    put_child_primitive(("a", "b", "c", "d"), "value", "test", tx)

    # Delete intermediate container
    delete_container(("a", "b"), tx)

    assert node_exists(("a",), tx)  # Parent still exists
    assert not node_exists(("a", "b"), tx)
    assert not node_exists(("a", "b", "c"), tx)
    assert not node_exists(("a", "b", "c", "d"), tx)
    assert not node_exists(("a", "b", "c", "d", "value"), tx)


# ============================================================================
# DESCENDANTS DELETION TESTS
# ============================================================================


def test_delete_descendants_basic(tx: TransactionProtocol) -> None:
    """Test basic descendants deletion."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    delete_descendants(("users",), tx)

    assert not node_exists(("users",), tx)


def test_delete_descendants_with_children(tx: TransactionProtocol) -> None:
    """Test delete_descendants removes all descendants."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    put_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    delete_descendants(("users",), tx)

    assert not node_exists(("users",), tx)
    assert not node_exists(("users", "alice"), tx)
    assert not node_exists(("users", "bob"), tx)


def test_delete_descendants_deep_hierarchy(tx: TransactionProtocol) -> None:
    """Test delete_descendants with deeply nested structure."""
    # Create: users -> alice -> profile -> settings
    create_container(
        ("users", "alice", "profile", "settings"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )
    put_child_primitive(("users", "alice", "profile", "settings"), "theme", "dark", tx)

    delete_descendants(("users", "alice"), tx)

    assert node_exists(("users",), tx)  # Parent still exists
    assert not node_exists(("users", "alice"), tx)


def test_delete_descendants_mixed_children(tx: TransactionProtocol) -> None:
    """Test delete_descendants with mixed containers and primitives."""
    create_container(
        ("root",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Add primitive children
    put_child_primitive(("root",), "p1", "value1", tx)
    put_child_primitive(("root",), "p2", "value2", tx)

    # Add container children
    create_container(
        ("root", "c1"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    put_child_primitive(("root", "c1"), "nested", "value", tx)

    delete_descendants(("root",), tx)

    assert not node_exists(("root",), tx)


def test_delete_descendants_nonexistent(tx: TransactionProtocol) -> None:
    """Test delete_descendants on nonexistent site is silent (idempotent)."""
    # Should not raise - silent operation
    delete_descendants(("nonexistent",), tx)


# ============================================================================
# EDGE CASES AND INTEGRATION
# ============================================================================


def test_create_delete_create_cycle(tx: TransactionProtocol) -> None:
    """Test creating, deleting, then recreating container works correctly."""
    # Create
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    assert node_exists(("users",), tx)

    # Delete
    delete_container(("users",), tx)
    assert not node_exists(("users",), tx)

    # Recreate
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    assert node_exists(("users",), tx)


def test_delete_preserves_siblings(tx: TransactionProtocol) -> None:
    """Test deleting container preserves sibling containers."""
    create_container(
        ("root",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("root", "a"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("root", "b"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("root", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Delete one child
    delete_container(("root", "b"), tx)

    # Verify siblings still exist
    assert node_exists(("root",), tx)
    assert node_exists(("root", "a"), tx)
    assert not node_exists(("root", "b"), tx)
    assert node_exists(("root", "c"), tx)


def test_parent_validation_integration(tx: TransactionProtocol) -> None:
    """Test parent validation works correctly in complex scenarios."""
    # Create partial hierarchy
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("a", "b"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Create deep child with ensure_healthy_parents=True
    # Should succeed because existing parents are healthy
    create_container(
        ("a", "b", "c", "d"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )

    assert node_exists(("a", "b", "c"), tx)  # Missing parent was created
    assert node_exists(("a", "b", "c", "d"), tx)
