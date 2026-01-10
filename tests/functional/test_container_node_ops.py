"""Functional tests for node operations.

Tests node identification and information gathering operations:
- node_exists() - checking node existence
- get_node_type() - getting node type
- get_node_info() - comprehensive node information
- gather_parent_info() - parent chain analysis
"""

from everyshape.container import (
    ContainerProtocol,
    ContainerStructure,
    create_container,
    gather_parent_info,
    get_node_info,
    get_node_type,
    node_exists,
    set_child_primitive,
)
from everyshape.container.types import NodeType
from everyshape.storage import TransactionProtocol


# ============================================================================
# NODE EXISTENCE TESTS
# ============================================================================


def test_node_exists_nonexistent(tx: TransactionProtocol) -> None:
    """Test node_exists returns False for nonexistent path."""
    assert not node_exists(("users",), tx)
    assert not node_exists(("users", "alice"), tx)


def test_node_exists_container(tx: TransactionProtocol) -> None:
    """Test node_exists returns True for existing container."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert node_exists(("users",), tx)


def test_node_exists_primitive(tx: TransactionProtocol) -> None:
    """Test node_exists returns True for existing primitive."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "name", "Alice", tx)

    assert node_exists(("users", "name"), tx)


# ============================================================================
# NODE TYPE TESTS
# ============================================================================


def test_get_node_type_nonexistent(tx: TransactionProtocol) -> None:
    """Test get_node_type returns NOT_FOUND for nonexistent path."""
    assert get_node_type(("users",), tx) == NodeType.NOT_FOUND


def test_get_node_type_container(tx: TransactionProtocol) -> None:
    """Test get_node_type returns CONTAINER for container nodes."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    assert get_node_type(("users",), tx) == NodeType.CONTAINER


def test_get_node_type_primitive(tx: TransactionProtocol) -> None:
    """Test get_node_type returns PRIMITIVE for primitive nodes."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "name", "Alice", tx)

    assert get_node_type(("users", "name"), tx) == NodeType.PRIMITIVE


def test_get_node_type_various_primitives(tx: TransactionProtocol) -> None:
    """Test get_node_type correctly identifies various primitive types."""
    create_container(
        ("data",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Different primitive types
    set_child_primitive(("data",), "string", "hello", tx)
    set_child_primitive(("data",), "number", 42, tx)
    set_child_primitive(("data",), "float", 3.14, tx)
    set_child_primitive(("data",), "bool", True, tx)
    set_child_primitive(("data",), "none", None, tx)

    # All should be PRIMITIVE
    assert get_node_type(("data", "string"), tx) == NodeType.PRIMITIVE
    assert get_node_type(("data", "number"), tx) == NodeType.PRIMITIVE
    assert get_node_type(("data", "float"), tx) == NodeType.PRIMITIVE
    assert get_node_type(("data", "bool"), tx) == NodeType.PRIMITIVE
    assert get_node_type(("data", "none"), tx) == NodeType.PRIMITIVE


# ============================================================================
# NODE INFO TESTS
# ============================================================================


def test_get_node_info_nonexistent(tx: TransactionProtocol) -> None:
    """Test get_node_info for nonexistent path."""
    info = get_node_info(("users",), tx)

    assert info.path == ("users",)
    assert not info.exists
    assert info.node_type == NodeType.NOT_FOUND
    assert info.structure is None
    assert info.protocol is None


def test_get_node_info_container(tx: TransactionProtocol) -> None:
    """Test get_node_info returns complete container information."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    info = get_node_info(("users",), tx)

    assert info.path == ("users",)
    assert info.exists
    assert info.node_type == NodeType.CONTAINER
    assert info.structure == ContainerStructure(1)
    assert info.protocol == ContainerProtocol.MUTABLE


def test_get_node_info_primitive(tx: TransactionProtocol) -> None:
    """Test get_node_info returns complete primitive information."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("users",), "name", "Alice", tx)

    info = get_node_info(("users", "name"), tx)

    assert info.path == ("users", "name")
    assert info.exists
    assert info.node_type == NodeType.PRIMITIVE
    assert info.primitive_value == "Alice"
    assert info.structure is None
    assert info.protocol is None


def test_get_node_info_various_container_protocols(tx: TransactionProtocol) -> None:
    """Test get_node_info correctly identifies different container protocols."""
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

    info1 = get_node_info(("c1",), tx)
    assert info1.protocol == ContainerProtocol.NONE
    assert info1.structure == ContainerStructure(1)

    info2 = get_node_info(("c2",), tx)
    assert info2.protocol == ContainerProtocol.MUTABLE
    assert info2.structure == ContainerStructure(2)

    info3 = get_node_info(("c3",), tx)
    assert info3.protocol == ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
    assert info3.structure == ContainerStructure(3)


# ============================================================================
# PARENT INFO GATHERING TESTS
# ============================================================================


def test_gather_parent_info_root_level(tx: TransactionProtocol) -> None:
    """Test gather_parent_info for root-level path has no parents."""
    parent_info = gather_parent_info(("users",), tx)

    assert len(parent_info.chain) == 0
    assert len(parent_info.missing_paths) == 0
    assert len(parent_info.malformed_paths) == 0
    assert parent_info.all_exist
    assert parent_info.all_healthy


def test_gather_parent_info_all_exist(tx: TransactionProtocol) -> None:
    """Test gather_parent_info when all parents exist."""
    # Create parent chain: a -> b -> c
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

    parent_info = gather_parent_info(("a", "b", "c"), tx)

    assert len(parent_info.chain) == 2
    assert len(parent_info.missing_paths) == 0
    assert len(parent_info.malformed_paths) == 0
    assert parent_info.all_exist
    assert parent_info.all_healthy

    # Check parent chain details
    assert parent_info.chain[0].path == ("a",)
    assert parent_info.chain[0].exists
    assert parent_info.chain[0].structure == ContainerStructure(1)
    assert parent_info.chain[0].protocol == ContainerProtocol.MUTABLE

    assert parent_info.chain[1].path == ("a", "b")
    assert parent_info.chain[1].exists


def test_gather_parent_info_missing_parent(tx: TransactionProtocol) -> None:
    """Test gather_parent_info detects missing parents."""
    parent_info = gather_parent_info(("a", "b", "c"), tx)

    assert len(parent_info.chain) == 2
    assert len(parent_info.missing_paths) == 2
    assert not parent_info.all_exist
    assert parent_info.all_healthy

    # Both parents should be missing
    assert ("a",) in parent_info.missing_paths
    assert ("a", "b") in parent_info.missing_paths


def test_gather_parent_info_partially_missing(tx: TransactionProtocol) -> None:
    """Test gather_parent_info when some parents exist, some missing."""
    # Create only the first parent
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    parent_info = gather_parent_info(("a", "b", "c"), tx)

    assert len(parent_info.chain) == 2
    assert len(parent_info.missing_paths) == 1
    assert not parent_info.all_exist

    # Only ("a", "b") should be missing
    assert ("a", "b") in parent_info.missing_paths
    assert ("a",) not in parent_info.missing_paths


def test_gather_parent_info_malformed_parent(tx: TransactionProtocol) -> None:
    """Test gather_parent_info detects malformed parents (primitives at parent locations)."""
    # Create a primitive where parent should be
    create_container(
        ("a",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("a",), "b", "wrong", tx)

    parent_info = gather_parent_info(("a", "b", "c"), tx)

    assert len(parent_info.chain) == 2
    assert len(parent_info.malformed_paths) == 1
    assert not parent_info.all_healthy

    # ("a", "b") should be malformed (it's a primitive, not a container)
    assert ("a", "b") in parent_info.malformed_paths


def test_gather_parent_info_deep_hierarchy(tx: TransactionProtocol) -> None:
    """Test gather_parent_info with deep path hierarchy."""
    # Create deep chain: a -> b -> c -> d -> e
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
    create_container(
        ("a", "b", "c"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    create_container(
        ("a", "b", "c", "d"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    parent_info = gather_parent_info(("a", "b", "c", "d", "e"), tx)

    assert len(parent_info.chain) == 4
    assert parent_info.all_exist
    assert parent_info.all_healthy

    # Verify parent chain is in correct order (root to immediate parent)
    assert parent_info.chain[0].path == ("a",)
    assert parent_info.chain[1].path == ("a", "b")
    assert parent_info.chain[2].path == ("a", "b", "c")
    assert parent_info.chain[3].path == ("a", "b", "c", "d")


def test_gather_parent_info_multiple_malformed(tx: TransactionProtocol) -> None:
    """Test gather_parent_info when multiple parents are malformed."""
    # Create primitives at multiple parent positions
    create_container(
        ("root",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )
    set_child_primitive(("root",), "a", "wrong1", tx)

    # Can't create ("root", "a", "b") as primitive because parent is primitive
    # So we'll test with what we can create
    parent_info = gather_parent_info(("root", "a", "b", "c"), tx)

    assert not parent_info.all_healthy
    assert ("root", "a") in parent_info.malformed_paths


# ============================================================================
# EDGE CASES AND INTEGRATION
# ============================================================================


def test_node_operations_after_deletion(tx: TransactionProtocol) -> None:
    """Test node operations correctly reflect state after deletion."""
    create_container(
        ("users",),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
        ensure_healthy_parents=False,
    )

    # Verify it exists
    assert node_exists(("users",), tx)
    assert get_node_type(("users",), tx) == NodeType.CONTAINER

    # Delete it directly using context (bypass delete_container which uses scan)
    tx.delete(("users",))

    # Verify node operations reflect deletion
    assert not node_exists(("users",), tx)
    assert get_node_type(("users",), tx) == NodeType.NOT_FOUND

    info = get_node_info(("users",), tx)
    assert not info.exists
    assert info.node_type == NodeType.NOT_FOUND


def test_node_operations_consistency(tx: TransactionProtocol) -> None:
    """Test all node operations return consistent results."""
    create_container(
        ("users",),
        ContainerStructure(5),
        ContainerProtocol.MUTABLE | ContainerProtocol.SIZED,
        tx,
        ensure_healthy_parents=False,
    )

    # All operations should agree
    exists = node_exists(("users",), tx)
    node_type = get_node_type(("users",), tx)
    info = get_node_info(("users",), tx)

    assert exists is True
    assert node_type == NodeType.CONTAINER
    assert info.exists is True
    assert info.node_type == NodeType.CONTAINER
    assert info.structure == ContainerStructure(5)
    assert info.protocol == ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
