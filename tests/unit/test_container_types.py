"""Unit tests for container types module."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from everyshape._types import NOT_SET
from everyshape.container.types import (
    DEFAULT_PARENT_PROTOCOL,
    DEFAULT_PARENT_STRUCTURE,
    ContainerProtocol,
    ContainerStructure,
    NodeInfo,
    NodeType,
    ParentChainInfo,
    ParentInfo,
    require_read_context,
    require_readwrite_context,
    require_snapshot,
    require_transaction,
    require_write_batch,
    require_write_context,
)
from everyshape.storage import (
    ReadAccessProtocol,
    ReadWriteAccessProtocol,
    SnapshotProtocol,
    StorageInterfaceError,
    TransactionProtocol,
    WriteAccessProtocol,
    WriteBatchProtocol,
)


# ========================================================
# NodeType Tests
# ========================================================


class TestNodeTypeEnum:
    """Tests for NodeType enum."""

    def test_node_type_primitive_exists(self) -> None:
        """Test that PRIMITIVE node type exists."""
        assert NodeType.PRIMITIVE is not None
        assert isinstance(NodeType.PRIMITIVE, NodeType)

    def test_node_type_container_exists(self) -> None:
        """Test that CONTAINER node type exists."""
        assert NodeType.CONTAINER is not None
        assert isinstance(NodeType.CONTAINER, NodeType)

    def test_node_type_not_found_exists(self) -> None:
        """Test that NOT_FOUND node type exists."""
        assert NodeType.NOT_FOUND is not None
        assert isinstance(NodeType.NOT_FOUND, NodeType)

    def test_node_type_str_primitive(self) -> None:
        """Test __str__ returns correct value for PRIMITIVE."""
        assert str(NodeType.PRIMITIVE) == "PRIMITIVE"

    def test_node_type_str_container(self) -> None:
        """Test __str__ returns correct value for CONTAINER."""
        assert str(NodeType.CONTAINER) == "CONTAINER"

    def test_node_type_str_not_found(self) -> None:
        """Test __str__ returns correct value for NOT_FOUND."""
        assert str(NodeType.NOT_FOUND) == "NOT_FOUND"

    def test_node_type_equality(self) -> None:
        """Test that enum values can be compared."""
        assert NodeType.PRIMITIVE == NodeType.PRIMITIVE
        assert NodeType.PRIMITIVE != NodeType.CONTAINER
        assert NodeType.CONTAINER != NodeType.NOT_FOUND


# ========================================================
# NodeInfo Tests
# ========================================================


class TestNodeInfo:
    """Tests for NodeInfo NamedTuple."""

    def test_node_info_creation_minimal(self) -> None:
        """Test creating NodeInfo with minimal required fields."""
        key = Mock()
        node_info = NodeInfo(
            path=key,
            exists=True,
            node_type=NodeType.PRIMITIVE,
        )

        assert node_info.path is key
        assert node_info.exists is True
        assert node_info.node_type == NodeType.PRIMITIVE

    def test_node_info_with_all_fields(self) -> None:
        """Test creating NodeInfo with all fields."""
        key = Mock()
        container_structure = ContainerStructure(42)
        container_protocol = ContainerProtocol.MUTABLE
        raw_value = "test_raw"
        primitive_value = "test_primitive"

        node_info = NodeInfo(
            path=key,
            exists=True,
            node_type=NodeType.CONTAINER,
            raw_value=raw_value,
            structure=container_structure,
            protocol=container_protocol,
            primitive_value=primitive_value,
        )

        assert node_info.path is key
        assert node_info.exists is True
        assert node_info.node_type == NodeType.CONTAINER
        assert node_info.raw_value == raw_value
        assert node_info.structure == container_structure
        assert node_info.protocol == container_protocol
        assert node_info.primitive_value == primitive_value

    def test_node_info_default_not_set_values(self) -> None:
        """Test that default values are NOT_SET."""
        key = Mock()
        node_info = NodeInfo(
            path=key,
            exists=False,
            node_type=NodeType.NOT_FOUND,
        )

        assert node_info.raw_value == NOT_SET
        assert node_info.structure is None
        assert node_info.protocol is None
        assert node_info.primitive_value == NOT_SET

    def test_node_info_field_access(self) -> None:
        """Test accessing NodeInfo fields by index and name."""
        key = Mock()
        node_info = NodeInfo(
            path=key,
            exists=True,
            node_type=NodeType.PRIMITIVE,
        )

        # Access by name
        assert node_info.path is key
        assert node_info.exists is True
        assert node_info.node_type == NodeType.PRIMITIVE

        # Access by index
        assert node_info[0] is key
        assert node_info[1] is True
        assert node_info[2] == NodeType.PRIMITIVE

    def test_node_info_immutable(self) -> None:
        """Test that NodeInfo is immutable."""
        key = Mock()
        node_info = NodeInfo(
            path=key,
            exists=True,
            node_type=NodeType.PRIMITIVE,
        )

        with pytest.raises(AttributeError):
            node_info.exists = False  # type: ignore


# ========================================================
# ParentInfo Tests
# ========================================================


class TestParentInfo:
    """Tests for ParentInfo NamedTuple."""

    def test_parent_info_creation_minimal(self) -> None:
        """Test creating ParentInfo with minimal required fields."""
        key = Mock()
        parent_info = ParentInfo(
            path=key,
            exists=True,
        )

        assert parent_info.path is key
        assert parent_info.exists is True

    def test_parent_info_with_all_fields(self) -> None:
        """Test creating ParentInfo with all fields."""
        key = Mock()
        container_structure = ContainerStructure(123)
        container_protocol = ContainerProtocol.INDEXED
        raw_type_data = {"type": "dict"}

        parent_info = ParentInfo(
            path=key,
            exists=True,
            structure=container_structure,
            protocol=container_protocol,
            raw_type_data=raw_type_data,
        )

        assert parent_info.path is key
        assert parent_info.exists is True
        assert parent_info.structure == container_structure
        assert parent_info.protocol == container_protocol
        assert parent_info.raw_type_data == raw_type_data

    def test_parent_info_default_none_values(self) -> None:
        """Test that default values for optional fields are None or NOT_SET."""
        key = Mock()
        parent_info = ParentInfo(
            path=key,
            exists=False,
        )

        assert parent_info.structure is None
        assert parent_info.protocol is None
        assert parent_info.raw_type_data == NOT_SET

    def test_parent_info_missing_parent(self) -> None:
        """Test ParentInfo for non-existent parent."""
        key = Mock()
        parent_info = ParentInfo(
            path=key,
            exists=False,
        )

        assert parent_info.exists is False
        assert parent_info.structure is None
        assert parent_info.protocol is None

    def test_parent_info_field_access(self) -> None:
        """Test accessing ParentInfo fields by index and name."""
        key = Mock()
        parent_info = ParentInfo(
            path=key,
            exists=True,
        )

        # Access by name
        assert parent_info.path is key
        assert parent_info.exists is True

        # Access by index
        assert parent_info[0] is key
        assert parent_info[1] is True


# ========================================================
# ParentChainInfo Tests
# ========================================================


class TestParentChainInfo:
    """Tests for ParentChainInfo NamedTuple."""

    def test_parent_chain_info_creation_empty(self) -> None:
        """Test creating ParentChainInfo with empty chain."""
        chain_info = ParentChainInfo(
            chain=(),
            missing_paths=(),
            malformed_paths=(),
        )

        assert chain_info.chain == ()
        assert chain_info.missing_paths == ()
        assert chain_info.malformed_paths == ()

    def test_parent_chain_info_with_parents(self) -> None:
        """Test creating ParentChainInfo with multiple parents."""
        key1 = Mock()
        key2 = Mock()
        key3 = Mock()

        parent1 = ParentInfo(path=key1, exists=True)
        parent2 = ParentInfo(path=key2, exists=True)
        parent3 = ParentInfo(path=key3, exists=False)

        chain_info = ParentChainInfo(
            chain=(parent1, parent2, parent3),
            missing_paths=(key3,),
            malformed_paths=(),
        )

        assert len(chain_info.chain) == 3
        assert chain_info.chain[0].path is key1
        assert chain_info.chain[1].path is key2
        assert chain_info.chain[2].path is key3

    def test_parent_chain_all_exist_true_when_no_missing(self) -> None:
        """Test all_exist property returns True when no missing paths."""
        key1 = Mock()
        key2 = Mock()

        parent1 = ParentInfo(path=key1, exists=True)
        parent2 = ParentInfo(path=key2, exists=True)

        chain_info = ParentChainInfo(
            chain=(parent1, parent2),
            missing_paths=(),
            malformed_paths=(),
        )

        assert chain_info.all_exist is True

    def test_parent_chain_all_exist_false_when_missing(self) -> None:
        """Test all_exist property returns False when missing paths."""
        key1 = Mock()
        key2 = Mock()

        parent1 = ParentInfo(path=key1, exists=True)
        parent2 = ParentInfo(path=key2, exists=False)

        chain_info = ParentChainInfo(
            chain=(parent1, parent2),
            missing_paths=(key2,),
            malformed_paths=(),
        )

        assert chain_info.all_exist is False

    def test_parent_chain_all_healthy_true_when_no_malformed(self) -> None:
        """Test all_healthy property returns True when no malformed paths."""
        key1 = Mock()
        key2 = Mock()

        parent1 = ParentInfo(path=key1, exists=True)
        parent2 = ParentInfo(path=key2, exists=True)

        chain_info = ParentChainInfo(
            chain=(parent1, parent2),
            missing_paths=(),
            malformed_paths=(),
        )

        assert chain_info.all_healthy is True

    def test_parent_chain_all_healthy_false_when_malformed(self) -> None:
        """Test all_healthy property returns False when malformed paths."""
        key1 = Mock()
        key2 = Mock()

        parent1 = ParentInfo(path=key1, exists=True)
        parent2 = ParentInfo(path=key2, exists=True)

        chain_info = ParentChainInfo(
            chain=(parent1, parent2),
            missing_paths=(),
            malformed_paths=(key2,),
        )

        assert chain_info.all_healthy is False

    def test_parent_chain_properties_both_false(self) -> None:
        """Test properties when both missing and malformed paths exist."""
        key1 = Mock()
        key2 = Mock()
        key3 = Mock()

        parent1 = ParentInfo(path=key1, exists=True)
        parent2 = ParentInfo(path=key2, exists=False)
        parent3 = ParentInfo(path=key3, exists=True)

        chain_info = ParentChainInfo(
            chain=(parent1, parent2, parent3),
            missing_paths=(key2,),
            malformed_paths=(key3,),
        )

        assert chain_info.all_exist is False
        assert chain_info.all_healthy is False

    def test_parent_chain_info_field_access(self) -> None:
        """Test accessing ParentChainInfo fields by index and name."""
        key = Mock()
        parent = ParentInfo(path=key, exists=True)

        chain_info = ParentChainInfo(
            chain=(parent,),
            missing_paths=(),
            malformed_paths=(),
        )

        # Access by name
        assert chain_info.chain == (parent,)
        assert chain_info.missing_paths == ()
        assert chain_info.malformed_paths == ()

        # Access by index
        assert chain_info[0] == (parent,)
        assert chain_info[1] == ()
        assert chain_info[2] == ()


# ========================================================
# ContainerStructure Tests
# ========================================================


class TestContainerStructure:
    """Tests for ContainerStructure NewType."""

    def test_container_structure_creation(self) -> None:
        """Test creating ContainerStructure from int."""
        struct = ContainerStructure(0)
        assert struct == 0

    def test_container_structure_different_values(self) -> None:
        """Test ContainerStructure with different integer values."""
        struct1 = ContainerStructure(42)
        struct2 = ContainerStructure(123)

        assert struct1 == 42
        assert struct2 == 123
        assert struct1 != struct2

    def test_container_structure_in_arithmetic(self) -> None:
        """Test ContainerStructure works in arithmetic operations."""
        struct = ContainerStructure(10)
        result = struct + 5

        assert result == 15

    def test_container_structure_comparison(self) -> None:
        """Test ContainerStructure comparison operations."""
        struct1 = ContainerStructure(5)
        struct2 = ContainerStructure(10)

        assert struct1 < struct2
        assert struct2 > struct1
        assert struct1 <= struct2
        assert struct2 >= struct1

    def test_container_structure_default_constant(self) -> None:
        """Test DEFAULT_PARENT_STRUCTURE constant."""
        assert DEFAULT_PARENT_STRUCTURE == 0
        assert isinstance(DEFAULT_PARENT_STRUCTURE, int)


# ========================================================
# ContainerProtocol Tests
# ========================================================


class TestContainerProtocol:
    """Tests for ContainerProtocol IntFlag enum."""

    def test_container_protocol_none(self) -> None:
        """Test NONE flag is 0."""
        assert ContainerProtocol.NONE == 0

    def test_container_protocol_mutable(self) -> None:
        """Test MUTABLE flag is 1 (2^0)."""
        assert ContainerProtocol.MUTABLE == 1

    def test_container_protocol_sized(self) -> None:
        """Test SIZED flag is 2 (2^1)."""
        assert ContainerProtocol.SIZED == 2

    def test_container_protocol_indexed(self) -> None:
        """Test INDEXED flag is 4 (2^2)."""
        assert ContainerProtocol.INDEXED == 4

    def test_container_protocol_mapping(self) -> None:
        """Test MAPPING flag is 8 (2^3)."""
        assert ContainerProtocol.MAPPING == 8

    def test_container_protocol_set(self) -> None:
        """Test SET flag is 16 (2^4)."""
        assert ContainerProtocol.SET == 16

    def test_container_protocol_bitwise_or(self) -> None:
        """Test combining flags with bitwise OR."""
        combined = ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
        assert combined == 3  # 1 | 2 = 3

    def test_container_protocol_bitwise_and(self) -> None:
        """Test checking flags with bitwise AND."""
        combined = ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
        assert (combined & ContainerProtocol.MUTABLE) == ContainerProtocol.MUTABLE
        assert (combined & ContainerProtocol.INDEXED) == 0

    def test_container_protocol_str_mutable(self) -> None:
        """Test __str__ for MUTABLE flag."""
        assert str(ContainerProtocol.MUTABLE) == "MUTABLE"

    def test_container_protocol_str_none(self) -> None:
        """Test __str__ for NONE flag."""
        assert str(ContainerProtocol.NONE) == ""

    def test_container_protocol_str_combined(self) -> None:
        """Test __str__ for combined flags with MUTABLE."""
        combined = ContainerProtocol.MUTABLE | ContainerProtocol.SIZED
        # Only MUTABLE is included in __str__ output
        assert "MUTABLE" in str(combined)

    def test_container_protocol_multiple_flags(self) -> None:
        """Test multiple flags combined."""
        combined = ContainerProtocol.MUTABLE | ContainerProtocol.SIZED | ContainerProtocol.INDEXED
        assert combined == 7  # 1 | 2 | 4 = 7

    def test_container_protocol_default_constant(self) -> None:
        """Test DEFAULT_PARENT_PROTOCOL constant."""
        assert DEFAULT_PARENT_PROTOCOL == ContainerProtocol.NONE
        assert DEFAULT_PARENT_PROTOCOL == 0

    def test_container_protocol_in_condition(self) -> None:
        """Test checking flag presence."""
        protocol = ContainerProtocol.MUTABLE | ContainerProtocol.INDEXED

        if protocol & ContainerProtocol.MUTABLE:
            mutable = True
        else:
            mutable = False

        if protocol & ContainerProtocol.SIZED:
            sized = True
        else:
            sized = False

        assert mutable is True
        assert sized is False


# ========================================================
# Context Guard Function Tests
# ========================================================


class TestRequireReadContext:
    """Tests for require_read_context guard function."""

    def test_require_read_context_with_valid_protocol(self) -> None:
        """Test require_read_context accepts ReadAccessProtocol."""
        mock_ctx = Mock(spec=ReadAccessProtocol)
        result = require_read_context(mock_ctx)

        assert result is mock_ctx

    def test_require_read_context_with_invalid_protocol(self) -> None:
        """Test require_read_context rejects non-ReadAccessProtocol."""
        invalid_ctx = object()

        with pytest.raises(StorageInterfaceError) as exc_info:
            require_read_context(invalid_ctx)

        assert "read access" in str(exc_info.value).lower()

    def test_require_read_context_caching(self) -> None:
        """Test that require_read_context caches results."""
        mock_ctx = Mock(spec=ReadAccessProtocol)

        result1 = require_read_context(mock_ctx)
        result2 = require_read_context(mock_ctx)

        assert result1 is result2 is mock_ctx


class TestRequireWriteContext:
    """Tests for require_write_context guard function."""

    def test_require_write_context_with_valid_protocol(self) -> None:
        """Test require_write_context accepts WriteAccessProtocol."""
        mock_ctx = Mock(spec=WriteAccessProtocol)
        result = require_write_context(mock_ctx)

        assert result is mock_ctx

    def test_require_write_context_with_invalid_protocol(self) -> None:
        """Test require_write_context rejects non-WriteAccessProtocol."""
        invalid_ctx = object()

        with pytest.raises(StorageInterfaceError) as exc_info:
            require_write_context(invalid_ctx)

        assert "write access" in str(exc_info.value).lower()

    def test_require_write_context_caching(self) -> None:
        """Test that require_write_context caches results."""
        mock_ctx = Mock(spec=WriteAccessProtocol)

        result1 = require_write_context(mock_ctx)
        result2 = require_write_context(mock_ctx)

        assert result1 is result2 is mock_ctx


class TestRequireReadWriteContext:
    """Tests for require_readwrite_context guard function."""

    def test_require_readwrite_context_with_valid_protocol(self) -> None:
        """Test require_readwrite_context accepts ReadWriteAccessProtocol."""
        mock_ctx = Mock(spec=ReadWriteAccessProtocol)
        result = require_readwrite_context(mock_ctx)

        assert result is mock_ctx

    def test_require_readwrite_context_with_invalid_protocol(self) -> None:
        """Test require_readwrite_context rejects invalid protocol."""
        invalid_ctx = object()

        with pytest.raises(StorageInterfaceError) as exc_info:
            require_readwrite_context(invalid_ctx)

        assert "read" in str(exc_info.value).lower()
        assert "write" in str(exc_info.value).lower()

    def test_require_readwrite_context_caching(self) -> None:
        """Test that require_readwrite_context caches results."""
        mock_ctx = Mock(spec=ReadWriteAccessProtocol)

        result1 = require_readwrite_context(mock_ctx)
        result2 = require_readwrite_context(mock_ctx)

        assert result1 is result2 is mock_ctx


class TestRequireTransaction:
    """Tests for require_transaction guard function."""

    def test_require_transaction_with_valid_protocol(self) -> None:
        """Test require_transaction accepts TransactionProtocol."""
        mock_ctx = Mock(spec=TransactionProtocol)
        result = require_transaction(mock_ctx)

        assert result is mock_ctx

    def test_require_transaction_with_invalid_protocol(self) -> None:
        """Test require_transaction rejects non-TransactionProtocol."""
        invalid_ctx = object()

        with pytest.raises(StorageInterfaceError) as exc_info:
            require_transaction(invalid_ctx)

        assert "transaction" in str(exc_info.value).lower()

    def test_require_transaction_caching(self) -> None:
        """Test that require_transaction caches results."""
        mock_ctx = Mock(spec=TransactionProtocol)

        result1 = require_transaction(mock_ctx)
        result2 = require_transaction(mock_ctx)

        assert result1 is result2 is mock_ctx


class TestRequireSnapshot:
    """Tests for require_snapshot guard function."""

    def test_require_snapshot_with_valid_protocol(self) -> None:
        """Test require_snapshot accepts SnapshotProtocol."""
        mock_ctx = Mock(spec=SnapshotProtocol)
        result = require_snapshot(mock_ctx)

        assert result is mock_ctx

    def test_require_snapshot_with_invalid_protocol(self) -> None:
        """Test require_snapshot rejects non-SnapshotProtocol."""
        invalid_ctx = object()

        with pytest.raises(StorageInterfaceError) as exc_info:
            require_snapshot(invalid_ctx)

        assert "snapshot" in str(exc_info.value).lower()

    def test_require_snapshot_caching(self) -> None:
        """Test that require_snapshot caches results."""
        mock_ctx = Mock(spec=SnapshotProtocol)

        result1 = require_snapshot(mock_ctx)
        result2 = require_snapshot(mock_ctx)

        assert result1 is result2 is mock_ctx


class TestRequireWriteBatch:
    """Tests for require_write_batch guard function."""

    def test_require_write_batch_with_valid_protocol(self) -> None:
        """Test require_write_batch accepts WriteBatchProtocol."""
        mock_ctx = Mock(spec=WriteBatchProtocol)
        result = require_write_batch(mock_ctx)

        assert result is mock_ctx

    def test_require_write_batch_with_invalid_protocol(self) -> None:
        """Test require_write_batch rejects non-WriteBatchProtocol."""
        invalid_ctx = object()

        with pytest.raises(StorageInterfaceError) as exc_info:
            require_write_batch(invalid_ctx)

        assert "write-batch" in str(exc_info.value).lower()

    def test_require_write_batch_caching(self) -> None:
        """Test that require_write_batch caches results."""
        mock_ctx = Mock(spec=WriteBatchProtocol)

        result1 = require_write_batch(mock_ctx)
        result2 = require_write_batch(mock_ctx)

        assert result1 is result2 is mock_ctx


# ========================================================
# Integration Tests
# ========================================================


class TestIntegration:
    """Integration tests across multiple types."""

    def test_node_info_with_container_and_protocol(self) -> None:
        """Test NodeInfo for a container node with protocol."""
        key = Mock()
        structure = ContainerStructure(99)
        protocol = ContainerProtocol.MUTABLE | ContainerProtocol.SIZED

        node_info = NodeInfo(
            path=key,
            exists=True,
            node_type=NodeType.CONTAINER,
            structure=structure,
            protocol=protocol,
        )

        assert node_info.node_type == NodeType.CONTAINER
        assert node_info.structure == structure
        assert (node_info.protocol & ContainerProtocol.MUTABLE) != 0
        assert (node_info.protocol & ContainerProtocol.SIZED) != 0

    def test_parent_chain_complete_hierarchy(self) -> None:
        """Test building a complete parent chain."""
        key1 = Mock(name="root")
        key2 = Mock(name="parent")
        key3 = Mock(name="grandparent")
        key4 = Mock(name="missing_ancestor")

        structure = ContainerStructure(1)
        protocol = ContainerProtocol.INDEXED

        parent1 = ParentInfo(
            path=key1,
            exists=True,
            structure=structure,
            protocol=protocol,
        )
        parent2 = ParentInfo(
            path=key2,
            exists=True,
            structure=structure,
            protocol=protocol,
        )
        parent3 = ParentInfo(path=key3, exists=True)
        parent4 = ParentInfo(
            path=key4,
            exists=False,
        )

        chain_info = ParentChainInfo(
            chain=(parent1, parent2, parent3, parent4),
            missing_paths=(key4,),
            malformed_paths=(),
        )

        assert chain_info.all_exist is False
        assert chain_info.all_healthy is True
        assert len(chain_info.chain) == 4

    def test_context_guards_with_mixed_protocols(self) -> None:
        """Test context guards properly distinguish between protocols."""
        read_only = Mock(spec=ReadAccessProtocol)
        write_only = Mock(spec=WriteAccessProtocol)
        read_write = Mock(spec=ReadWriteAccessProtocol)

        # Each should accept its own protocol
        assert require_read_context(read_only) is read_only
        assert require_write_context(write_only) is write_only
        assert require_readwrite_context(read_write) is read_write

        # Mixed protocols should fail appropriately
        with pytest.raises(StorageInterfaceError):
            require_read_context(write_only)

        with pytest.raises(StorageInterfaceError):
            require_write_context(read_only)
