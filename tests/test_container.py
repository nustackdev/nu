"""Comprehensive tests for Container class.

These tests validate the Container interface works correctly and maintains
safety guarantees.
"""

import pathlib
from collections.abc import Generator

import pytest

from redwood.storage import StorageProtocol, TransactionProtocol
from redwood.tree import (
    Container,
    ContainerProtocol,
    ContainerStructure,
    InvalidPathError,
    NodeType,
    PathExistsError,
    PathNotFoundError,
    PathTypeError,
)
from redwood.types import EMPTY


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def storage(tmp_path: pathlib.Path) -> Generator[StorageProtocol, None, None]:
    """Create temporary storage backend for testing."""
    from rwstd.storage.codecs import BinaryCodec
    from rwstd.storage.storage_rocksdb import RocksDBStorage

    db_path = tmp_path / "test_db"
    storage = RocksDBStorage(path=db_path, codec=BinaryCodec())
    storage.open()
    yield storage  # type: ignore
    storage.close()


@pytest.fixture
def tx(storage: StorageProtocol) -> Generator[TransactionProtocol, None, None]:
    """Create transaction context."""
    with storage.transaction() as tx:
        yield tx


# ============================================================================
# CONTAINER CREATION TESTS
# ============================================================================


def test_create_container_basic(tx: TransactionProtocol) -> None:
    """Test basic container creation."""
    container = Container.create(
        path=("/", "users"),
        ctx=tx,
        structure=ContainerStructure(1),
        protocol=ContainerProtocol.MUTABLE,
    )

    print(container)
    assert container.path == ("/", "users")
    assert container.exists()

    info = container.info()
    assert info.path == ("/", "users")
    assert info.exists
    assert info.node_type == NodeType.CONTAINER
    assert info.structure == ContainerStructure(1)
    assert info.protocol == ContainerProtocol.MUTABLE


def test_create_with_parents(tx: TransactionProtocol) -> None:
    """Test container creation with automatic parent creation."""
    container = Container.create(
        path=("/", "a", "b", "c"),
        ctx=tx,
        structure=ContainerStructure(1),
        protocol=ContainerProtocol.MUTABLE,
        ensure_healthy_parents=True,
    )

    assert container.exists()

    # Verify parents were created
    parent_b = Container.get(("/", "a", "b"), tx)
    assert parent_b.exists()

    parent_a = Container.get(
        (
            "/",
            "a",
        ),
        tx,
    )
    assert parent_a.exists()


def test_create_noroot_raises(tx: TransactionProtocol) -> None:
    """Test creating duplicate container raises error."""
    with pytest.raises(InvalidPathError):
        Container.create(
            ("users",),
            tx,
            ContainerStructure(1),
            ContainerProtocol.MUTABLE,
        )


def test_create_duplicate_raises(tx: TransactionProtocol) -> None:
    """Test creating duplicate container raises error."""
    Container.create(("/", "users"), tx, ContainerStructure(1), ContainerProtocol.MUTABLE)

    with pytest.raises(PathExistsError):
        Container.create(("/", "users"), tx, ContainerStructure(2), ContainerProtocol.MUTABLE)


def test_get_existing_container(tx: TransactionProtocol) -> None:
    """Test getting existing container."""
    # Create first
    Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Get it
    container = Container.get(
        ("/", "users"),
        tx,
    )
    assert container.exists()
    assert container.path == ("/", "users")


def test_get_nonexistent_raises(tx: TransactionProtocol) -> None:
    """Test getting nonexistent container raises error."""
    with pytest.raises(PathNotFoundError):
        Container.get(
            (
                "/",
                "nonexistent",
            ),
            tx,
        )


def test_get_primitive_raises(tx: TransactionProtocol) -> None:
    """Test getting primitive as container raises error."""
    from redwood.tree import create_container, set_child_primitive

    # Create parent
    create_container(
        ("/", "data"),
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        tx,
    )

    # Create primitive child
    set_child_primitive(
        ("/", "data"),
        "value",
        "test",
        tx,
    )

    # Try to get primitive as container
    with pytest.raises(PathTypeError):
        Container.get(("/", "data", "value"), tx)


# ============================================================================
# INTROSPECTION TESTS
# ============================================================================


def test_info_reflects_current_state(tx: TransactionProtocol) -> None:
    """Test info() always reflects current storage state."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # First info call
    info1 = container.info()
    assert info1.exists
    assert info1.structure == ContainerStructure(1)

    # External deletion
    from redwood.tree import delete_container

    delete_container(("/", "users"), tx)

    # Info should reflect deletion
    info2 = container.info()
    assert not info2.exists


def test_exists_reflects_current_state(tx: TransactionProtocol) -> None:
    """Test exists() always reflects current storage state."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    assert container.exists()

    # External deletion
    from redwood.tree import delete_container

    delete_container(("/", "users"), tx)

    # Should detect deletion
    assert not container.exists()


def test_node_type(tx: TransactionProtocol) -> None:
    """Test node_type() returns CONTAINER."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    assert container.node_type() == NodeType.CONTAINER


def test_parent_chain_info(tx: TransactionProtocol) -> None:
    """Test parent_chain_info() returns health information."""
    container = Container.create(
        path=("/", "a", "b", "c"),
        ctx=tx,
        structure=ContainerStructure(1),
        protocol=ContainerProtocol.MUTABLE,
        ensure_healthy_parents=True,
    )

    chain_info = container.parent_chain_info()
    assert chain_info.all_exist
    assert chain_info.all_healthy
    assert len(chain_info.chain) == 3  # Parents: ("/",), ("/", "a") and ("/", "a", "b")


# ============================================================================
# CHILD QUERY TESTS
# ============================================================================


def test_has_child(tx: TransactionProtocol) -> None:
    """Test has_child() checks child existence."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    assert not container.has_child("alice")

    container.set_child_primitive("alice", {"name": "Alice"})

    assert container.has_child("alice")


def test_get_child_type(tx: TransactionProtocol) -> None:
    """Test get_child_type() returns correct type."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Nonexistent child
    assert container.get_child_type("alice") == NodeType.NOT_FOUND

    # Primitive child
    container.set_child_primitive("alice", {"name": "Alice"})
    assert container.get_child_type("alice") == NodeType.PRIMITIVE

    # Container child
    container.create_child_container("posts", ContainerStructure(2), ContainerProtocol.MUTABLE)
    assert container.get_child_type("posts") == NodeType.CONTAINER


def test_list_child_keys(tx: TransactionProtocol) -> None:
    """Test list_child_keys() returns all child keys."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Empty initially
    assert set(container.list_child_keys()) == set()

    # Add children
    container.set_child_primitive("alice", {"name": "Alice"})
    container.set_child_primitive("bob", {"name": "Bob"})
    container.create_child_container("posts", ContainerStructure(2), ContainerProtocol.MUTABLE)

    keys = container.list_child_keys()
    print(keys)
    assert set(keys) == {"alice", "bob", "posts"}


def test_list_children(tx: TransactionProtocol) -> None:
    """Test list_children() returns full paths."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.set_child_primitive("alice", {"name": "Alice"})
    container.set_child_primitive("bob", {"name": "Bob"})

    keys = []
    values = []
    for k, v in container.list_children():
        keys.append(k)
        values.append(v)

    assert set(keys) == {"alice", "bob"}


def test_count_children(tx: TransactionProtocol) -> None:
    """Test count_children() returns correct count."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    assert container.count_children() == 0

    container.set_child_primitive("alice", {"name": "Alice"})
    assert container.count_children() == 1

    container.set_child_primitive("bob", {"name": "Bob"})
    assert container.count_children() == 2


# ============================================================================
# CHILD CREATION TESTS
# ============================================================================


def test_create_child_container(tx: TransactionProtocol) -> None:
    """Test creating child containers."""
    parent = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    child = parent.create_child_container("alice", ContainerStructure(1), ContainerProtocol.MUTABLE)

    assert child.path == ("/", "users", "alice")
    assert child.exists()
    assert parent.has_child("alice")


def test_create_child_container_duplicate_raises(tx: TransactionProtocol) -> None:
    """Test creating duplicate child container raises error."""
    parent = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    parent.create_child_container("alice", ContainerStructure(1), ContainerProtocol.MUTABLE)

    with pytest.raises(PathExistsError):
        parent.create_child_container("alice", ContainerStructure(2), ContainerProtocol.MUTABLE)


def test_set_child_primitive(tx: TransactionProtocol) -> None:
    """Test setting primitive children."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.set_child_primitive("name", "Alice")
    container.set_child_primitive("age", 30)

    assert container.has_child("name")
    assert container.has_child("age")


def test_set_child_primitive_update(tx: TransactionProtocol) -> None:
    """Test updating primitive child."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.set_child_primitive("name", "Alice")
    assert container.get_child_primitive("name") == "Alice"

    container.set_child_primitive("name", "Alice Smith")
    assert container.get_child_primitive("name") == "Alice Smith"


def test_set_child_primitive_over_container_raises(tx: TransactionProtocol) -> None:
    """Test setting primitive over container raises error."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.create_child_container("posts", ContainerStructure(2), ContainerProtocol.MUTABLE)

    with pytest.raises(PathTypeError):
        container.set_child_primitive("posts", "invalid")


def test_get_child_primitive(tx: TransactionProtocol) -> None:
    """Test getting primitive child."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Nonexistent returns EMPTY
    value = container.get_child_primitive("name")
    assert value is EMPTY

    # Set and get
    container.set_child_primitive("name", "Alice")
    value = container.get_child_primitive("name")
    assert value == "Alice"


def test_get_child_primitive_container_raises(tx: TransactionProtocol) -> None:
    """Test getting container as primitive raises error."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.create_child_container("posts", ContainerStructure(2), ContainerProtocol.MUTABLE)

    with pytest.raises(PathTypeError):
        container.get_child_primitive("posts")


# ============================================================================
# CHILD DELETION TESTS
# ============================================================================


def test_delete_child_primitive(tx: TransactionProtocol) -> None:
    """Test deleting primitive child."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.set_child_primitive("name", "Alice")
    assert container.has_child("name")

    result = container.delete_child("name")
    assert result is True
    assert not container.has_child("name")


def test_delete_child_container_recursive(tx: TransactionProtocol) -> None:
    """Test deleting container child with recursive=True."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    child = container.create_child_container(
        "posts", ContainerStructure(2), ContainerProtocol.MUTABLE
    )
    child.set_child_primitive("post1", "First post")

    result = container.delete_child("posts")
    assert result is True
    assert not container.has_child("posts")


def test_delete_child_nonexistent(tx: TransactionProtocol) -> None:
    """Test deleting nonexistent child returns False."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    result = container.delete_child("nonexistent")
    assert result is False


def test_clear_children(tx: TransactionProtocol) -> None:
    """Test clearing all children."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.set_child_primitive("alice", {"name": "Alice"})
    container.set_child_primitive("bob", {"name": "Bob"})
    container.create_child_container("posts", ContainerStructure(2), ContainerProtocol.MUTABLE)

    count = container.clear_children()
    assert count == 3
    assert container.count_children() == 0


# ============================================================================
# DESCENDANT TESTS
# ============================================================================


def test_list_descendants(tx: TransactionProtocol) -> None:
    """Test listing all descendants."""
    root = Container.create(
        ("/", "root"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Build tree: root -> a -> b -> c
    a = root.create_child_container("a", ContainerStructure(1), ContainerProtocol.MUTABLE)
    b = a.create_child_container("b", ContainerStructure(1), ContainerProtocol.MUTABLE)
    c = b.create_child_container("c", ContainerStructure(1), ContainerProtocol.MUTABLE)
    c.set_child_primitive("value", "test")

    descendants = list(root.list_descendants())
    print(descendants)
    assert len(descendants) >= 4  # At least a, b, c, and value


def test_list_descendants_max_depth(tx: TransactionProtocol) -> None:
    """Test listing descendants with depth limit."""
    root = Container.create(
        (
            "/",
            "root",
        ),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Build tree: root -> a -> b -> c
    a = root.create_child_container("a", ContainerStructure(1), ContainerProtocol.MUTABLE)
    b = a.create_child_container("b", ContainerStructure(1), ContainerProtocol.MUTABLE)
    b.create_child_container("c", ContainerStructure(1), ContainerProtocol.MUTABLE)

    # Only immediate children
    descendants = list(root.list_descendants(depth=1))
    assert len(descendants) == 1  # Only 'a'


def test_walk_tree(tx: TransactionProtocol) -> None:
    """Test tree walking iteration."""
    root = Container.create(
        (
            "/",
            "root",
        ),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    root.set_child_primitive("prim1", "value1")
    child = root.create_child_container("cont1", ContainerStructure(1), ContainerProtocol.MUTABLE)
    child.set_child_primitive("prim2", "value2")

    results = list(root.walk_tree())
    paths = [path for path, _ in results]
    types = [node_type for _, node_type in results]

    assert ("/", "root", "prim1") in paths
    assert ("/", "root", "cont1") in paths
    assert ("/", "root", "cont1", "prim2") in paths

    assert NodeType.PRIMITIVE in types
    assert NodeType.CONTAINER in types


# ============================================================================
# SELF DESTRUCTION TESTS
# ============================================================================


def test_delete_self(tx: TransactionProtocol) -> None:
    """Test deleting container itself."""
    container = Container.create(
        (
            "/",
            "temp",
        ),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    assert container.exists()

    result = container.delete()
    assert result is True
    assert not container.exists()


def test_delete_self_makes_instance_invalid(tx: TransactionProtocol) -> None:
    """Test container instance becomes invalid after deletion."""
    container = Container.create(
        ("/", "temp"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    container.delete()

    info = container.info()
    assert not info.exists

    # Further operations should fail
    with pytest.raises(PathNotFoundError):
        container.set_child_primitive("key", "value")


# ============================================================================
# VALIDATION TESTS
# ============================================================================


def test_validate_compatible(tx: TransactionProtocol) -> None:
    """Test type compatibility validation."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Should pass - exact match
    container.validate_compatible(ContainerStructure(1), ContainerProtocol.MUTABLE)

    # Should fail - wrong structure
    with pytest.raises(PathTypeError):
        container.validate_compatible(ContainerStructure(2), ContainerProtocol.MUTABLE)


def test_get_child_container(tx: TransactionProtocol) -> None:
    """Test convenience method for getting child containers."""
    parent = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    parent.create_child_container("alice", ContainerStructure(1), ContainerProtocol.MUTABLE)

    child = parent.get_child_container("alice")
    assert child.path == ("/", "users", "alice")
    assert child.exists()


def test_get_child_container_nonexistent_raises(tx: TransactionProtocol) -> None:
    """Test get_child_container raises on nonexistent child."""
    parent = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    with pytest.raises(PathNotFoundError):
        parent.get_child_container("nonexistent")


def test_get_child_container_primitive_raises(tx: TransactionProtocol) -> None:
    """Test get_child_container raises on primitive child."""
    parent = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    parent.set_child_primitive("name", "Alice")

    with pytest.raises(PathTypeError):
        parent.get_child_container("name")


# ============================================================================
# SAFETY TESTS (The Critical Ones!)
# ============================================================================


def test_safety_no_stale_data_after_external_deletion(tx: TransactionProtocol) -> None:
    """Test container detects external deletions (no stale data bug)."""
    # This is the key test for the stale data problem
    a = Container.create(
        (
            "/",
            "A",
        ),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    b = a.create_child_container("B", ContainerStructure(1), ContainerProtocol.MUTABLE)

    # External deletion (simulates your scenario 1)
    from redwood.tree import delete_container

    delete_container(("/", "A", "B"), tx)

    # b should detect the deletion
    assert not b.exists()

    # Operations on b should fail correctly
    with pytest.raises(PathNotFoundError):
        b.set_child_primitive("C", "value")


def test_safety_parent_validation_prevents_orphans(tx: TransactionProtocol) -> None:
    """Test parent validation prevents orphaned nodes."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Delete container
    from redwood.tree import delete_container

    delete_container(("/", "users"), tx)

    # Try to add child to deleted container
    with pytest.raises(PathNotFoundError):
        container.set_child_primitive("alice", {"name": "Alice"})


def test_safety_type_enforcement(tx: TransactionProtocol) -> None:
    """Test type safety prevents replacing containers with primitives."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # Create container child
    container.create_child_container("posts", ContainerStructure(2), ContainerProtocol.MUTABLE)

    # Can't replace container with primitive
    with pytest.raises(PathTypeError):
        container.set_child_primitive("posts", "wrong")


def test_safety_parent_chain_integrity(tx: TransactionProtocol) -> None:
    """Test parent chain must be healthy."""
    # Create deep path
    container = Container.create(
        ("/", "a", "b", "c"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
        ensure_healthy_parents=True,
    )

    # Verify all parents exist
    chain_info = container.parent_chain_info()
    assert chain_info.all_exist
    assert chain_info.all_healthy


# ============================================================================
# PERFORMANCE/CACHING TESTS
# ============================================================================


def test_transaction_caching_makes_validation_fast(tx: TransactionProtocol) -> None:
    """Test that transaction caching makes repeated validations fast."""
    import time

    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    # First batch: should be fast (transaction caches parent checks)
    start = time.time()
    for i in range(100):
        container.set_child_primitive(f"user{i}", {"id": i})
    elapsed = time.time() - start

    # Should complete quickly (< 1 second even with validation)
    # Note: Actual timing depends on hardware and storage backend
    assert elapsed < 1.0, f"100 operations took {elapsed:.2f}s (too slow)"

    # Verify all were created
    assert container.count_children() == 100


# ============================================================================
# USAGE PATTERN TESTS
# ============================================================================


def test_typical_usage_pattern(tx: TransactionProtocol) -> None:
    """Test typical usage pattern from docs."""
    # Create root
    users = Container.create(("/", "users"), tx, ContainerStructure(1), ContainerProtocol.MUTABLE)

    alice = users.create_child_container("alice", ContainerStructure(1), ContainerProtocol.MUTABLE)

    # Add data
    alice.set_child_primitive("name", "Alice")
    alice.set_child_primitive("age", 30)
    alice.set_child_primitive("email", "alice@example.com")

    # Query
    assert alice.has_child("name")
    assert alice.get_child_primitive("name") == "Alice"
    assert alice.count_children() == 3

    # Navigate
    assert set(alice.list_child_keys()) == {"name", "age", "email"}


def test_error_recovery_pattern(tx: TransactionProtocol) -> None:
    """Test error recovery pattern with accurate state."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    try:
        # Simulate some operation that might fail
        container.set_child_primitive("alice", {"name": "Alice"})

        # Delete container (simulating external deletion)
        from redwood.tree import delete_container

        delete_container(("/", "users"), tx)

        # Try to add another child (will fail)
        container.set_child_primitive("bob", {"name": "Bob"})

    except PathNotFoundError:
        # Can reliably check current state for error recovery
        assert not container.exists()  # Accurate!

        # Can make informed decision
        if not container.exists():
            # Re-create container
            new_container = Container.create(
                ("/", "users"),
                tx,
                ContainerStructure(1),
                ContainerProtocol.MUTABLE,
            )
            assert new_container.exists()


def test_repr_and_str(tx: TransactionProtocol) -> None:
    """Test string representations."""
    container = Container.create(
        ("/", "users"),
        tx,
        ContainerStructure(1),
        ContainerProtocol.MUTABLE,
    )

    repr_str = repr(container)
    assert "Container" in repr_str
    assert "users" in repr_str

    str_str = str(container)
    assert "Container" in str_str
    assert "users" in str_str
