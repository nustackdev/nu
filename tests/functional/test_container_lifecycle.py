"""Functional tests for container lifecycle operations.

Tests container creation, deletion, and subtree operations:
- create_container() - creating containers with parent validation
- delete_container() - deleting containers
- delete_subtree() - recursive deletion
- create_parents() - automatic parent creation
"""

import pytest

from everyshape.container import (
    ContainerProtocol,
    ContainerStructure,
    PathExistsError,
    PathTypeError,
    create_container,
    create_parents,
    delete_container,
    delete_subtree,
    get_node_info,
    get_node_type,
    node_exists,
    set_child_primitive,
)
from everyshape.container.types import NodeType
from everyshape.storage import TransactionProtocol


# ============================================================================
# CONTAINER CREATION TESTS
# ============================================================================


def test_create_container_basic(tx: TransactionProtocol) -> None:
    """Test basic container creation without parent validation."""
    created = create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert created is True
    assert node_exists(("users",), tx)
    assert get_node_type(("users",), tx) == NodeType.CONTAINER

    info = get_node_info(("users",), tx)
    assert info.structure == ContainerStructure(1)
    assert info.protocol == ContainerProtocol.MUTABLE


def test_create_container_idempotent_compatible(tx: TransactionProtocol) -> None:
    """Test creating container twice with same type is idempotent."""
    created1 = create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    created2 = create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert created1 is True
    assert created2 is False  # Already exists


def test_create_container_incompatible_type_raises(tx: TransactionProtocol) -> None:
    """Test creating container with incompatible type raises error."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    with pytest.raises(PathExistsError):
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
    set_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(PathTypeError):
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
    created = create_container(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )

    assert created is True

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
    created = create_container(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert created is True
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
    set_child_primitive(("a",), "b", "wrong", tx)

    with pytest.raises(PathTypeError):  # ParentMalformedError is subclass of PathTypeError
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
    created = create_parents(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert len(created) == 2
    assert ("a",) in created
    assert ("a", "b") in created

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

    created = create_parents(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert len(created) == 1
    assert ("a", "b") in created
    assert ("a",) not in created  # Already existed


def test_create_parents_all_exist(tx: TransactionProtocol) -> None:
    """Test create_parents returns empty list when all parents exist."""
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

    created = create_parents(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert len(created) == 0


def test_create_parents_malformed_raises(tx: TransactionProtocol) -> None:
    """Test create_parents raises when parent is malformed."""
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("a",), "b", "wrong", tx)

    with pytest.raises(PathTypeError):  # ParentMalformedError is subclass of PathTypeError
        create_parents(
            ("a", "b", "c"),
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
            tx,
        )


def test_create_parents_root_level(tx: TransactionProtocol) -> None:
    """Test create_parents for root-level path returns empty list."""
    created = create_parents(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    assert len(created) == 0


# ============================================================================
# CONTAINER DELETION TESTS
# Note: These tests require scan operations which MemoryStorage doesn't support
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

    deleted = delete_container(("users",), tx)

    assert deleted is True
    assert not node_exists(("users",), tx)


def test_delete_container_nonexistent(tx: TransactionProtocol) -> None:
    """Test deleting nonexistent container returns False."""
    deleted = delete_container(("users",), tx)

    assert deleted is False


def test_delete_container_primitive_raises(tx: TransactionProtocol) -> None:
    """Test deleting primitive as container raises error."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("data",), "value", 42, tx)

    with pytest.raises(PathTypeError):
        delete_container(("data", "value"), tx)


def test_delete_container_with_children(tx: TransactionProtocol) -> None:
    """Test deleting container with children deletes entire subtree."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    set_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    deleted = delete_container(("users",), tx)

    assert deleted is True
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
    set_child_primitive(("a", "b", "c", "d"), "value", "test", tx)

    # Delete intermediate container
    deleted = delete_container(("a", "b"), tx)

    assert deleted is True
    assert node_exists(("a",), tx)  # Parent still exists
    assert not node_exists(("a", "b"), tx)
    assert not node_exists(("a", "b", "c"), tx)
    assert not node_exists(("a", "b", "c", "d"), tx)
    assert not node_exists(("a", "b", "c", "d", "value"), tx)


# ============================================================================
# SUBTREE DELETION TESTS
# Note: These tests require scan operations which MemoryStorage doesn't support
# ============================================================================


def test_delete_subtree_basic(tx: TransactionProtocol) -> None:
    """Test basic subtree deletion."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    count = delete_subtree(("users",), tx)

    assert count == 1
    assert not node_exists(("users",), tx)


def test_delete_subtree_with_children(tx: TransactionProtocol) -> None:
    """Test delete_subtree counts all deleted nodes."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "alice", {"name": "Alice"}, tx)
    set_child_primitive(("users",), "bob", {"name": "Bob"}, tx)

    count = delete_subtree(("users",), tx)

    assert count == 3  # Container + 2 children
    assert not node_exists(("users",), tx)


def test_delete_subtree_deep_hierarchy(tx: TransactionProtocol) -> None:
    """Test delete_subtree with deeply nested structure."""
    # Create: users -> alice -> profile -> settings
    create_container(
        ("users", "alice", "profile", "settings"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )
    set_child_primitive(("users", "alice", "profile", "settings"), "theme", "dark", tx)

    count = delete_subtree(("users", "alice"), tx)

    # Should delete: alice (container), profile (container), settings (container), theme (primitive)
    assert count >= 4
    assert node_exists(("users",), tx)  # Parent still exists
    assert not node_exists(("users", "alice"), tx)


def test_delete_subtree_mixed_children(tx: TransactionProtocol) -> None:
    """Test delete_subtree with mixed containers and primitives."""
    create_container(
        ("root",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Add primitive children
    set_child_primitive(("root",), "p1", "value1", tx)
    set_child_primitive(("root",), "p2", "value2", tx)

    # Add container children
    create_container(
        ("root", "c1"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("root", "c1"), "nested", "value", tx)

    count = delete_subtree(("root",), tx)

    # Should delete: root, p1, p2, c1, nested = 5 nodes
    assert count == 5
    assert not node_exists(("root",), tx)


def test_delete_subtree_nonexistent(tx: TransactionProtocol) -> None:
    """Test delete_subtree on nonexistent path returns 0."""
    count = delete_subtree(("nonexistent",), tx)

    assert count == 0


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
    created = create_container(
        ("a", "b", "c", "d"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=True,
    )

    assert created is True
    assert node_exists(("a", "b", "c"), tx)  # Missing parent was created
    assert node_exists(("a", "b", "c", "d"), tx)
