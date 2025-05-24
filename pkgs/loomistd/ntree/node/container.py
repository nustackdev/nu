"""
ContainerNode implementation for the tree storage system.

This module implements ContainerNode following a filesystem mental model,
providing low-level storage operations without handling recursion or complex logic.
Views are responsible for interpreting and building on these operations.

IMPORTANT: This implementation combines three key concepts to achieve high performance
and safe concurrency:

**Immutability & Thread Safety**
Each ContainerNode is frozen (attrs.frozen=True) and cannot be modified after creation.
This eliminates race conditions in both async and threading environments since there's
no shared mutable state between concurrent operations.

**Transaction Hashing & Cache Isolation**
Every node is bound to a transaction with a stable hashing. This creates unique
hash values for each node-transaction pair, enabling safe method caching.
Nodes from different transactions get separate cache entries even with identical data,
preventing cross-transaction cache contamination without complex invalidation logic.
lru_cache cant be used directly due to the frozen nature, therefore
a separate self-cleaning cache is used.

**Operation Tracking & Conflict Detection**
The transaction system records all read operations through "get_for_update" tracking.
When methods like exists() or validate_parents_exist() access data, the transaction
logs these keys for optimistic concurrency control. If concurrent transactions touch
overlapping data, the system detects conflicts and handles them through retries or
explicit resolution.

**Example: Parent Validation**
The validate_parents_exist() method shows these concepts working together - it checks
and creates parent containers while the transaction tracks all accessed keys. The
immutable design prevents interference between concurrent operations, while caching
optimizes repeated calls within the same transaction boundary.

*Note that for true thread safety, the transaction object of an underlying
backend must also be thread-safe, as this implementation does not handle
concurrency at the transaction level.*

Quite elegant, huh?
"""

from __future__ import annotations

from typing import Any, Generator

import attrs

from loomistd.kv import StorageKeyError

from ..exceptions import ContainerProtocolError, PathTypeError
from ..path import DataPath, StructPath
from ..types import ContainerProtocol, ContainerStructure, NodeType
from .base import BaseNode

__all__ = [
    "ContainerNode",
]


@attrs.define(frozen=True, kw_only=True)
class ContainerNode(BaseNode):
    """
    Container node interface - provides filesystem-like operations for containers.

    Following a filesystem mental model:
    - ContainerNode handles storage, validation, and basic structural operations
    - Views provide protocol-specific interfaces and handle recursion
    - Two-path system separates user data (DataPath) from metadata (StructPath)

    Responsibilities:
    - Container lifecycle management (existence, creation)
    - Validation (parents, protocols, structure, mutability)
    - Primitive child operations (no recursion)
    - Structure queries (let views handle interpretation)
    - Metadata operations (view-specific data)
    """

    # Container structure (MAPPING_CONTAINER, SEQUENCE_CONTAINER, etc.)
    structure: ContainerStructure = attrs.field(kw_only=True)

    # Container protocol (MUTABLE, FLAT, etc.)
    protocol: ContainerProtocol = attrs.field(kw_only=True)

    # Derived struct path for metadata storage
    struct_path: StructPath = attrs.field(init=False)

    def __attrs_post_init__(self) -> None:
        """Initialize derived attributes after attrs initialization."""
        # Derive StructPath from DataPath components
        object.__setattr__(self, "struct_path", StructPath(*self.path.components[1:]))
        # (this is a bit hacky, but harmless)

    @property
    def node_type(self) -> NodeType:
        """Get the type of this node - always CONTAINER."""
        return NodeType.CONTAINER

    # =========================================================================
    # Validation Methods
    # =========================================================================

    def validate_compatibility(
        self, required_structure: ContainerStructure, required_protocol: ContainerProtocol
    ) -> None:
        """
        Validate container supports required structure and protocol.

        Args:
            required_structure: Structure that must be supported
            required_protocol: Protocol that must be supported

        Raises:
            ContainerProtocolError: If requirements not met
        """
        self.validate_structure(required_structure)
        self.validate_protocol(required_protocol)

    def validate_structure(self, required_structure: ContainerStructure) -> None:
        """
        Validate container supports required structure.

        Args:
            required_structure: Structure that must be supported

        Raises:
            ContainerProtocolError: If structure not supported
        """
        if not (self.structure & required_structure == required_structure):
            raise ContainerProtocolError(
                f"Container at {self.path} does not support structure {required_structure}. "
                f"Container has structure: {self.structure}"
            )

    def validate_protocol(self, required_protocol: ContainerProtocol) -> None:
        """
        Validate container supports required protocol.

        Args:
            required_protocol: Protocol that must be supported

        Raises:
            ContainerProtocolError: If protocol not supported
        """
        if not (self.protocol & required_protocol):
            raise ContainerProtocolError(
                f"Container at {self.path} does not support protocol {required_protocol}. "
                f"Container has protocol: {self.protocol}"
            )

    def validate_mutability(self) -> None:
        """
        Validate container supports MUTABLE protocol.

        Raises:
            ContainerProtocolError: If container is not mutable
        """
        self.validate_protocol(ContainerProtocol.MUTABLE)

    def validate_parents_exist(self) -> None:
        """
        Validate all parent containers exist.

        Creates parent containers as MAPPING containers if they don't exist.
        Also touches them for transaction concurrency safety (important for
        optimistic concurrency control in LMDB/RocksDB).

        Raises:
            PathTypeError: If parent path exists but is not a container
        """
        tx = self.get_ensured_transaction()

        parent_path = self.path.parent()
        if parent_path is None:
            # No parent path, we are on a root node, nothing to validate
            return

        # Check if parent exists
        try:
            tx.get(parent_path.to_tuple())

            # Verify it's a container
            type_info = tx.get(StructPath(*parent_path.components[1:]).to_tuple())

            if not isinstance(type_info, list) or len(type_info) != 2:
                raise PathTypeError(
                    f"Parent path {parent_path} exists but is not a valid container"
                )

            # Parent exists and is valid
            return

        except StorageKeyError:
            # Parent doesn't exist, create it
            parent_container = ContainerNode(
                backend=self.backend,
                path=parent_path,
                structure=ContainerStructure.MAPPING_CONTAINER,
                protocol=ContainerProtocol.DICT,
                tx=tx,
            )
            parent_container.ensure_exists()

    # =========================================================================
    # Container Lifecycle
    # =========================================================================

    def exists(self) -> bool:
        """
        Check if this container exists in storage.

        A container exists if:
        1. The data path exists in storage
        2. The type metadata exists and is valid
        3. The stored type matches this container's structure/protocol

        Raises:
            PathTypeError: If path exists but is not a valid container
            ContainerProtocolError: If existing container has different structure/protocol

        Returns:
            bool: True if container exists with matching type
        """
        tx = self.get_ensured_transaction()

        try:
            # Check type metadata
            type_info = tx.get(self.struct_path.to_tuple())

            # Ensure type info is a sequence with two elements (structure, protocol)
            if not isinstance(type_info, (list, tuple)) or len(type_info) != 2:
                raise PathTypeError(f"Path {self.path} exists but is not a valid container")

            stored_structure = ContainerStructure(type_info[0])
            stored_protocol = ContainerProtocol(type_info[1])

            # Verify type matches
            self.validate_compatibility(
                required_structure=stored_structure,
                required_protocol=stored_protocol,
            )

            return True

        except (StorageKeyError,):
            return False

    def create(self) -> None:
        """
        Create container in storage.

        Raises:
            PathTypeError: If path already exists with different type
        """
        tx = self.get_ensured_transaction()

        # Check if container already exists
        if self.exists():
            raise PathTypeError(f"Container at {self.path} already exists")

        # Ensure parent containers exist
        self.validate_parents_exist()

        # Store type metadata
        tx.set(self.struct_path.to_tuple(), [self.structure.value, self.protocol.value])

    def ensure_exists(self) -> None:
        """
        Convenience method: create container if it doesn't exist.

        Also ensures all parent containers exist as MAPPING containers.

        Raises:
            PathTypeError: If path exists but with incompatible type
            ContainerProtocolError: If existing container has different structure/protocol
        """
        if self.exists():
            return

        self.create()

    # =========================================================================
    # Child Operations
    # =========================================================================

    def get_primitive_value(self, key: str, default=None) -> Any:
        """
        Get primitive value for key. Does not handle nested containers.

        Args:
            key: Child key to get
            default: Default value if key doesn't exist or is not primitive

        Returns:
            Primitive value or default
        """
        tx = self.get_ensured_transaction()

        child_path = self.path.join(key)

        try:
            value = tx.get(child_path.to_tuple())
            return value if value is not self.EMPTY else default

        except StorageKeyError:
            return default

    def set_primitive_value(self, key: str, value: Any) -> None:
        """
        Set primitive value for key. Does not create nested containers.

        Args:
            key: Child key to set
            value: Primitive value to store

        Note:
            Views are responsible for creating nested containers if needed.
        """
        self.validate_mutability()

        tx = self.get_ensured_transaction()

        child_path = self.path.join(key)
        tx.set(child_path.to_tuple(), value)

    def delete_child(self, key: str) -> None:
        """
        Delete child (primitive or container) at key.

        For containers, recursively deletes all descendants.

        Args:
            key: Child key to delete

        Raises:
            KeyError: If child doesn't exist
        """
        self.validate_mutability()

        tx = self.get_ensured_transaction()

        if not self.has_child(key):
            raise KeyError(f"No child with key '{key}'")

        child_path = self.path.join(key)

        if self.is_child_container(key):
            # Delete all descendants
            self._delete_subtree(child_path)
        else:
            # Delete primitive
            tx.delete(child_path.to_tuple())

    def clear(self) -> None:
        """
        Clear all children (primitives and containers) in this container.

        Raises:
            KeyError: If container doesn't exist
        """
        self.validate_mutability()

        if not self.exists():
            raise KeyError(f"Container at {self.path} does not exist")

        # Delete all children
        for key in self.keys():
            try:
                self.delete_child(key)
            except KeyError:
                pass

    def _delete_subtree(self, path: DataPath) -> None:
        """
        Recursively delete a container and all its descendants.

        Args:
            path: Root path to delete
            tx: Transaction to use
        """
        tx = self.get_ensured_transaction()
        # Delete all data paths
        data_paths = list(tx.list_keys(path.to_tuple(), depth=-1))
        data_paths.sort(key=len, reverse=True)  # Delete deepest first

        for data_path in data_paths:
            try:
                tx.delete(data_path)
            except StorageKeyError:
                pass

        # Delete all struct paths
        struct_path = StructPath(*path.components[1:])
        struct_paths = list(tx.list_keys(struct_path.to_tuple(), depth=-1))
        struct_paths.sort(key=len, reverse=True)

        for s_path in struct_paths:
            try:
                tx.delete(s_path)
            except StorageKeyError:
                pass

        # Delete root paths
        try:
            tx.delete(path.to_tuple())
            tx.delete(struct_path.to_tuple())
        except StorageKeyError:
            pass

    # =========================================================================
    # Structure Queries
    # =========================================================================

    def is_child_container(self, key: str) -> bool:
        """
        Check if child at key is a container.

        Args:
            key: Child key to check

        Returns:
            bool: True if child exists and is a container
        """
        tx = self.get_ensured_transaction()

        child_path = self.path.join(key)
        child_struct_path = StructPath(*child_path.components[1:])

        try:
            tx.get(child_struct_path.to_tuple())
            return True
        except StorageKeyError:
            return False

    def is_child_primitive(self, key: str) -> bool:
        """
        Check if child at key is a primitive.

        Args:
            key: Child key to check

        Returns:
            bool: True if child exists and is a primitive
        """
        child_path = self.path.join(key)

        tx = self.get_ensured_transaction()

        try:
            tx.get(child_path.to_tuple())
            return True
        except StorageKeyError:
            return False

    def has_child(self, key: str) -> bool:
        """
        Check if child exists at key (container or primitive).

        Args:
            key: Child key to check

        Returns:
            bool: True if child exists
        """
        return self.is_child_container(key) or self.is_child_primitive(key)

    def keys(self, include_containers: bool = True) -> Generator[str, None, None]:
        """
        Get child keys.
        If include_containers is True, includes both primitive and container keys.
        Otherwise, only returns primitive keys.

        Args:
            include_containers (bool): Whether to include container keys
        Yields:
            str: Child keys (primitive or container)
        """

        tx = self.get_ensured_transaction()

        if not self.exists():
            return

        # List primitive keys
        for path_tuple in tx.list_keys(self.path.to_tuple(), depth=1):
            yield path_tuple[-1]  # Get last component (key)

        if not include_containers:
            return

        # List container keys
        for key in tx.list_keys(self.struct_path.to_tuple(), depth=1):
            yield key[-1]  # Get last component (key)

    # =========================================================================
    # Metadata Operations (View-Specific Data)
    # =========================================================================

    def get_metadata(self, key: str, default=None) -> Any:
        """
        Get metadata value (e.g., __length__ for ListView).

        Metadata is stored in the struct path namespace.

        Args:
            key: Metadata key
            default: Default value if not found

        Returns:
            Metadata value or default
        """
        tx = self.get_ensured_transaction()

        metadata_path = self.struct_path.join(key)
        try:
            return tx.get(metadata_path.to_tuple())
        except StorageKeyError:
            return default

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value (e.g., __length__ for ListView).

        Args:
            key: Metadata key
            value: Metadata value to store
        """
        tx = self.get_ensured_transaction()
        metadata_path = self.struct_path.join(key)
        tx.set(metadata_path.to_tuple(), value)

    def has_metadata(self, key: str) -> bool:
        """
        Check if metadata key exists.

        Args:
            key: Metadata key to check

        Returns:
            bool: True if metadata exists
        """
        tx = self.get_ensured_transaction()
        metadata_path = self.struct_path.join(key)
        return tx.exists(metadata_path.to_tuple())

    def delete_metadata(self, key: str) -> None:
        """
        Delete metadata key.

        Args:
            key: Metadata key to delete

        Raises:
            KeyError: If metadata doesn't exist
        """
        tx = self.get_ensured_transaction()
        metadata_path = self.struct_path.join(key)
        try:
            tx.delete(metadata_path.to_tuple())
        except StorageKeyError:
            raise KeyError(f"Metadata key '{key}' not found")
