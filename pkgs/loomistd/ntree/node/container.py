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
"""

from __future__ import annotations

import dataclasses
from enum import Enum, auto
from typing import Generator

import attrs

from loomistd.kv import StorageKeyError

from ..exceptions import ContainerProtocolError, PathExistsError, PathNotFoundError, PathTypeError
from ..path import Path
from ..types import (
    EMPTY,
    ContainerProtocol,
    ContainerStructure,
    Empty,
    NodeType,
    PathComponent,
    PathTuple,
    Value,
)
from .base import BaseNode

__all__ = [
    "ContainerNode",
    "ContainerState",
    "ParentInfo",
    "ContainerInfo",
    "ChildInfo",
    "ChildType",
]


class ChildType(Enum):
    """Simple child type classification."""

    PRIMITIVE = auto()
    CONTAINER = auto()
    NOT_FOUND = auto()


@dataclasses.dataclass(frozen=True)
class ChildInfo:
    """Basic information about a child."""

    key: PathComponent
    exists: bool
    child_type: ChildType
    value: Value | Empty = EMPTY  # For primitives


@dataclasses.dataclass(frozen=True)
class ParentInfo:
    """Raw information about a parent container."""

    path: Path
    exists: bool
    stored_structure: ContainerStructure | None = None
    stored_protocol: ContainerProtocol | None = None
    raw_type_data: Value | Empty = EMPTY  # Raw data from storage, could be malformed


@dataclasses.dataclass(frozen=True)
class ContainerInfo:
    """Pure information about container and parent chain - no validation logic."""

    # Container raw data
    exists: bool
    stored_structure: ContainerStructure | None = None
    stored_protocol: ContainerProtocol | None = None
    raw_type_data: Value | Empty = EMPTY  # Raw data from storage, could be malformed

    # Parent chain raw data (from root to immediate parent)
    parents: tuple[ParentInfo, ...] = dataclasses.field(default_factory=tuple)

    # Paths categorization (pure facts, no validation decisions)
    missing_parent_paths: tuple[Path, ...] = dataclasses.field(default_factory=tuple)
    malformed_parent_paths: tuple[Path, ...] = dataclasses.field(default_factory=tuple)


class ContainerState(Enum):
    """Container states after validation."""

    VALID = auto()  # Exists and matches expected type
    NOT_FOUND = auto()  # Doesn't exist
    TYPE_MISMATCH = auto()  # Exists but wrong type
    MALFORMED = auto()  # Exists but corrupted data


@attrs.define(frozen=True, kw_only=True)
class ContainerNode(BaseNode):
    """Container node implementation.

    Provides filesystem-like operations for containers with a layered architecture
    that cleanly separates information gathering, validation, feasibility checking,
    and operation execution.

    Architecture layers:
        - Information methods: Pure data gathering with no validation logic
        - Validation methods: Check conditions and raise errors on failure
        - Support methods: Boolean feasibility checks
        - Execution methods: Perform operations with proper validation
        - Convenience methods: Common operation patterns
        - Inspection methods: Simple state queries

    Attributes:
        structure: The expected container structure type.
        protocol: The expected container protocol flags.
    """

    structure: ContainerStructure = attrs.field(kw_only=True)
    protocol: ContainerProtocol = attrs.field(kw_only=True)

    @property
    def node_type(self) -> NodeType:
        """Get the type of this node.

        Returns:
            NodeType: Always returns NodeType.CONTAINER for container nodes.
        """
        return NodeType.CONTAINER

    # ========================================================================
    # MAIN CONTAINER OPERATIONS
    # ========================================================================

    # ------------------------------------------------------------------------
    # INFORMATION LAYER - Pure Data Gathering (No Validation Logic)
    # ------------------------------------------------------------------------

    def get_info(self) -> ContainerInfo:
        """Gather raw information about container and parent chain.

        This method performs pure data collection without making any validation
        decisions. It touches all relevant storage keys to ensure proper transaction
        read-locking and gathers comprehensive information about the container
        and its entire parent chain.

        The method traverses the path hierarchy from root to target, collecting
        raw storage data and categorizing paths based on existence and data format,
        but does not perform any validation logic or make decisions about whether
        the data is "valid" or "invalid" - that's left to validation methods.

        Returns:
            ContainerInfo: Raw data about container and parents including:
                - Container existence and stored type data
                - Parent chain information from root to immediate parent
                - Lists of missing and malformed parent paths
                - All raw storage data for further analysis

        Note:
            This method is always called first by other lifecycle methods to
            ensure proper transaction locking and provide data for validation.
            It does not raise exceptions - all error conditions are returned
            as data in the ContainerInfo object.
        """
        # Collect all paths to check (root to target)
        paths_to_check = self._get_path_chain()

        # Gather parent information
        parent_infos = []
        missing_paths = []
        malformed_paths = []

        # Check all parents (excluding target)
        for path in paths_to_check[:-1]:
            parent_info = self._get_path_info(path)
            parent_infos.append(parent_info)

            if not parent_info.exists:
                missing_paths.append(path)
            elif parent_info.stored_structure is None or parent_info.stored_protocol is None:
                # Malformed data
                malformed_paths.append(path)

        # Check target container
        target_path = paths_to_check[-1]
        target_info = self._get_path_info(target_path)

        return ContainerInfo(
            exists=target_info.exists,
            stored_structure=target_info.stored_structure,
            stored_protocol=target_info.stored_protocol,
            raw_type_data=target_info.raw_type_data,
            parents=tuple(parent_infos),
            missing_parent_paths=tuple(missing_paths),
            malformed_parent_paths=tuple(malformed_paths),
        )

    def _get_path_chain(self) -> list[Path]:
        """Get complete path chain from root to target container.

        Traverses from the target path up to the root, collecting all intermediate
        paths, then reverses the list to provide root-to-target ordering.

        Returns:
            list[Path]: Ordered list of paths from root to target, including
                the target path itself. Empty list if path has no parents.

        Example:
            For path '/a/b/c', returns [Path('/a'), Path('/a/b'), Path('/a/b/c')]
        """
        paths = []
        current = self.path
        while current is not None:
            paths.append(current)
            current = current.parent()
        return list(reversed(paths))

    def _get_path_info(self, path: Path) -> ParentInfo:
        """Get raw storage information for a single path.

        Retrieves raw type metadata from storage and attempts to parse it into
        structure and protocol enums. Does not validate compatibility or
        correctness - just extracts what's available.

        Args:
            path: The path to gather information about.

        Returns:
            ParentInfo: Raw information including:
                - Whether the path exists in storage
                - Parsed structure/protocol if data is well-formed
                - Raw storage data for malformed entries
                - None values for structure/protocol indicate malformed data

        Note:
            This method does not raise storage exceptions - missing keys result
            in exists=False, and malformed data results in None enum values.
        """
        tx = self.get_ensured_transaction()

        struct_path = path.struct_path

        try:
            raw_data = tx.get(struct_path.to_tuple())

            # Try to parse structure/protocol
            structure, protocol = None, None
            if isinstance(raw_data, (list, tuple)) and len(raw_data) == 2:
                try:
                    structure = ContainerStructure(raw_data[0])
                    protocol = ContainerProtocol(raw_data[1])
                except ValueError:
                    pass  # Keep as None - indicates malformed data

            return ParentInfo(
                path=path,
                exists=True,
                stored_structure=structure,
                stored_protocol=protocol,
                raw_type_data=raw_data,
            )

        except StorageKeyError:
            return ParentInfo(path=path, exists=False)

    # ------------------------------------------------------------------------
    # VALIDATION LAYER - Validates Conditions and Raises Errors
    # ------------------------------------------------------------------------

    def validate_exists(self, info: ContainerInfo, /) -> None:
        """Validate that the container exists in storage.

        Args:
            info: Container information from get_info().

        Raises:
            PathNotFoundError: If the container does not exist.

        Example:
            ```python
            info = container.get_info()
            container.validate_exists(info)  # Raises if not found
            ```
        """
        if not info.exists:
            raise PathNotFoundError(f"Container at {self.path} does not exist")

    def validate_not_exists(self, info: ContainerInfo, /) -> None:
        """Validate that the container does not exist in storage.

        Useful for create operations where the container should not already exist.

        Args:
            info: Container information from get_info().

        Raises:
            PathExistsError: If the container already exists.

        Example:
            ```python
            info = container.get_info()
            container.validate_not_exists(info)  # Raises if exists
            ```
        """
        if info.exists:
            raise PathExistsError(f"Container at {self.path} already exists")

    def validate_compatible(self, info: ContainerInfo, /) -> None:
        """Validate that the container type is compatible with expected structure/protocol.

        Checks that the container exists, has well-formed type data, and that
        both structure and protocol are compatible with this node's expectations.
        Structure compatibility uses bitwise AND to allow subset matching.
        Protocol compatibility requires at least one common flag.

        Args:
            info: Container information from get_info().

        Raises:
            PathNotFoundError: If the container does not exist.
            PathTypeError: If type data is malformed or incompatible.

        Example:
            ```python
            info = container.get_info()
            container.validate_compatible(info)  # Raises if incompatible
            ```
        """
        self.validate_exists(info)

        if info.stored_structure is None or info.stored_protocol is None:
            raise PathTypeError(
                f"Container at {self.path} has malformed type data: {info.raw_type_data}"
            )

        structure_match = self.structure & info.stored_structure == self.structure
        protocol_match = bool(self.protocol & info.stored_protocol)

        if not structure_match:
            raise PathTypeError(
                f"Structure mismatch at {self.path}: "
                f"expected {self.structure}, got {info.stored_structure}"
            )

        if not protocol_match:
            raise PathTypeError(
                f"Protocol mismatch at {self.path}: "
                f"expected {self.protocol}, got {info.stored_protocol}"
            )

    def validate_parents_exist(self, info: ContainerInfo, /) -> None:
        """Validate that all parent containers exist in storage.

        Args:
            info: Container information from get_info().

        Raises:
            PathNotFoundError: If any parent containers are missing.

        Example:
            ```python
            info = container.get_info()
            container.validate_parents_exist(info)  # Raises if parents missing
            ```
        """
        if info.missing_parent_paths:
            raise PathNotFoundError(f"Missing parent containers: {info.missing_parent_paths}")

    def validate_parents_healthy(self, info: ContainerInfo, /) -> None:
        """Validate that all parent containers have well-formed type data.

        Checks that existing parent containers have parseable structure and
        protocol information. Does not validate compatibility - only that
        the data format is correct.

        Args:
            info: Container information from get_info().

        Raises:
            PathTypeError: If any parent containers have malformed type data.

        Example:
            ```python
            info = container.get_info()
            container.validate_parents_healthy(info)  # Raises if data corrupted
            ```
        """
        if info.malformed_parent_paths:
            raise PathTypeError(f"Malformed parent containers: {info.malformed_parent_paths}")

    def validate_parents_chain(self, info: ContainerInfo, /) -> None:
        """Validate that the entire parent chain is valid and complete.

        Combines existence and health checks to ensure all parents exist
        and have well-formed type data. This is the comprehensive parent
        validation used when parent creation is not allowed.

        Args:
            info: Container information from get_info().

        Raises:
            PathNotFoundError: If any parent containers are missing.
            PathTypeError: If any parent containers have malformed type data.

        Example:
            ```python
            info = container.get_info()
            container.validate_parents_chain(info)  # Full parent validation
            ```
        """
        self.validate_parents_exist(info)
        self.validate_parents_healthy(info)

    def validate_mutable(self, info: ContainerInfo, /) -> None:
        """Validate that the container supports mutation operations.

        Checks that the container exists, is compatible with expected type,
        and has the MUTABLE protocol flag set. Required before any mutation
        operations like adding or removing children.

        Args:
            info: Container information from get_info().

        Raises:
            PathNotFoundError: If container does not exist.
            PathTypeError: If container is incompatible or has malformed data.
            ContainerProtocolError: If container is not mutable.

        Example:
            ```python
            info = container.get_info()
            container.validate_mutable(info)  # Raises if cannot mutate
            ```
        """
        self.validate_compatible(info)

        if info.stored_protocol is None:
            raise PathTypeError(f"Container at {self.path} has malformed protocol data")

        if ~(info.stored_protocol & ContainerProtocol.MUTABLE):
            raise ContainerProtocolError(f"Container at {self.path} is not mutable")

    def validate_createable(self, info: ContainerInfo, /, *, parents: bool = True) -> None:
        """Validate that container creation is possible.

        Checks conditions required for successful container creation, including
        non-existence of the target and parent chain requirements based on
        whether parent creation is allowed.

        Args:
            info: Container information from get_info().
            parents: Whether parent creation is allowed. If True, only malformed
                parents block creation. If False, complete parent chain required.

        Raises:
            PathExistsError: If container already exists.
            PathTypeError: If malformed parents prevent creation.
            PathNotFoundError: If parents=False and parents are missing.

        Example:
            ```python
            info = container.get_info()
            container.validate_createable(info, parents=True)  # Allow parent creation
            container.validate_createable(info, parents=False)  # Require existing parents
            ```
        """
        if info.exists:
            raise PathExistsError(f"Container at {self.path} already exists")

        if parents:
            # With parent creation, only malformed parents block creation
            self.validate_parents_healthy(info)
        else:
            # Without parent creation, need complete valid chain
            self.validate_parents_chain(info)

    def validate_parents_createable(self, info: ContainerInfo, /) -> None:
        """Validate that missing parent containers can be created.

        Checks that there are no malformed parents that would prevent creation
        of missing parents. Malformed parents cannot be automatically fixed
        and must be resolved manually.

        Args:
            info: Container information from get_info().

        Raises:
            PathTypeError: If malformed parents prevent creation.

        Example:
            ```python
            info = container.get_info()
            container.validate_parents_createable(info)  # Check if can create parents
            ```
        """
        # Only malformed parents prevent creation
        self.validate_parents_healthy(info)

    # ------------------------------------------------------------------------
    # SUPPORT LAYER - Boolean Feasibility Checks
    # ------------------------------------------------------------------------

    def supports_creation(self, info: ContainerInfo, /, *, parents: bool = True) -> bool:
        """Check if container creation is feasible without raising exceptions.

        Wrapper around validate_createable() that returns a boolean result
        instead of raising exceptions. Useful for conditional logic where
        you want to check feasibility before attempting creation.

        Args:
            info: Container information from get_info().
            parents: Whether parent creation should be considered feasible.

        Returns:
            bool: True if try_create() would succeed, False otherwise.

        Example:
            ```python
            info = container.get_info()
            if container.supports_creation(info):
                result = container.try_create(info)  # Guaranteed to succeed
            else:
                handle_creation_blocked()
            ```
        """
        try:
            self.validate_createable(info, parents=parents)
            return True
        except (PathExistsError, PathTypeError, ContainerProtocolError):
            return False

    def supports_mutation(self, info: ContainerInfo) -> bool:
        """Check if container mutation is feasible without raising exceptions.

        Wrapper around validate_mutable() that returns a boolean result.
        Useful for determining if mutation operations like add/remove children
        would be successful.

        Args:
            info: Container information from get_info().

        Returns:
            bool: True if mutation operations would succeed, False otherwise.

        Example:
            ```python
            info = container.get_info()
            if container.supports_mutation(info):
                # Safe to perform mutations
                container.add_child(key, value)
            ```
        """
        try:
            self.validate_mutable(info)
            return True
        except (PathNotFoundError, PathTypeError, ContainerProtocolError):
            return False

    def supports_compatibility(self, info: ContainerInfo) -> bool:
        """Check if container is compatible with expected type without raising exceptions.

        Wrapper around validate_compatible() that returns a boolean result.
        Useful for checking type compatibility in conditional logic.

        Args:
            info: Container information from get_info().

        Returns:
            bool: True if container matches expected structure/protocol, False otherwise.

        Example:
            ```python
            info = container.get_info()
            if container.supports_compatibility(info):
                # Container matches expected type
                proceed_with_operations()
            else:
                handle_type_mismatch()
            ```
        """
        try:
            self.validate_compatible(info)
            return True
        except (PathNotFoundError, PathTypeError, ContainerProtocolError):
            return False

    # ------------------------------------------------------------------------
    # EXECUTION LAYER - Performs Operations
    # ------------------------------------------------------------------------

    def try_create(self, info: ContainerInfo, *, parents: bool = True) -> bool:
        """Create the container if it doesn't exist.

        Attempts to create the container after validating that creation is
        possible. If the container already exists with compatible type,
        returns False without error. Creates missing parents if requested
        and needed.

        Args:
            info: Container information from get_info().
            parents: Whether to create missing parent containers automatically.

        Returns:
            bool: True if container was created, False if it already existed
                with compatible type.

        Raises:
            PathExistsError: If container exists but with incompatible type.
            PathTypeError: If type conflicts prevent creation.
            ContainerProtocolError: If protocol violations prevent creation.
            PathNotFoundError: If parents=False and parents are missing.

        Example:
            ```python
            info = container.get_info()
            try:
                created = container.try_create(info, parents=True)
                if created:
                    print("Container created successfully")
                else:
                    print("Container already existed")
            except PathTypeError as e:
                print(f"Type conflict: {e}")
            ```
        """
        # Handle already exists case
        if info.exists:
            if self.supports_compatibility(info):
                return False  # Already exists with compatible type
            else:
                # Exists but incompatible - validate will raise appropriate error
                self.validate_compatible(info)

        # Validate we can create
        self.validate_createable(info, parents=parents)

        # Create parents if needed
        if parents and info.missing_parent_paths:
            self.try_create_parents(info)

        # Create container
        tx = self.get_ensured_transaction()
        tx.set(self.path.struct_path.to_tuple(), [self.structure.value, self.protocol.value])

        return True

    def try_create_parents(self, info: ContainerInfo) -> list[Path]:
        """Create missing parent containers.

        Creates any missing parent containers using default MAPPING_CONTAINER
        structure and DICT protocol. Only creates parents that are actually
        missing - existing parents are left unchanged.

        Args:
            info: Container information from get_info().

        Returns:
            list[Path]: List of parent paths that were actually created.
                Empty list if no parents needed creation.

        Raises:
            PathTypeError: If malformed parent data prevents creation.

        Example:
            ```python
            info = container.get_info()
            try:
                created = container.try_create_parents(info)
                print(f"Created {len(created)} parent containers")
            except PathTypeError as e:
                print(f"Cannot create parents: {e}")
            ```

        Note:
            Created parents use MAPPING_CONTAINER|DICT which provides
            maximum compatibility for child container creation.
        """
        self.validate_parents_createable(info)

        if not info.missing_parent_paths:
            return []

        tx = self.get_ensured_transaction()
        created = []

        for parent_path in info.missing_parent_paths:
            tx.set(
                parent_path.struct_path.to_tuple(),
                [ContainerStructure.MAPPING_CONTAINER.value, ContainerProtocol.DICT.value],
            )
            created.append(parent_path)

        return created

    # ------------------------------------------------------------------------
    # CONVENIENCE LAYER - Common Operation Patterns
    # ------------------------------------------------------------------------

    def ensure_exists(self, info: ContainerInfo, *, parents: bool = True) -> bool:
        """Ensure container exists, creating if necessary or validating if present.

        High-level convenience method that handles both creation and validation
        scenarios. If container exists, validates compatibility. If missing,
        creates it with optional parent creation.

        Args:
            info: Container information from get_info().
            parents: Whether to create missing parent containers.

        Returns:
            bool: True if container was created, False if it already existed.

        Raises:
            PathTypeError: If existing container has incompatible type or
                if type conflicts prevent creation.
            ContainerProtocolError: If protocol violations occur.
            PathNotFoundError: If parents=False and parents are missing.

        Example:
            ```python
            info = container.get_info()
            created = container.ensure_exists(info, parents=True)
            # Now guaranteed: container exists and is compatible
            ```
        """
        if info.exists:
            self.validate_compatible(info)
            return False
        else:
            return self.try_create(info, parents=parents)

    def ensure_parents(self, info: ContainerInfo) -> list[Path]:
        """Ensure all parent containers exist, creating missing ones.

        Convenience method that ensures the entire parent chain is healthy
        and complete. Creates any missing parents and validates that existing
        parents have well-formed data.

        Args:
            info: Container information from get_info().

        Returns:
            list[Path]: List of parent paths that were created. Empty if
                all parents already existed.

        Raises:
            PathTypeError: If existing parents have malformed data that
                cannot be automatically resolved.

        Example:
            ```python
            info = container.get_info()
            created = container.ensure_parents(info)
            # Now guaranteed: all parents exist and are healthy
            ```
        """
        if not info.missing_parent_paths:
            self.validate_parents_healthy(info)  # Ensure existing parents are healthy
            return []

        return self.try_create_parents(info)

    # ========================================================================
    # CHILDREN OPERATIONS - Primitive and Container Subtrees
    # ========================================================================

    # ------------------------------------------------------------------------
    # INFORMATION LAYER - Simple Child Data Gathering
    # ------------------------------------------------------------------------

    def get_child_info(self, key: PathComponent, /) -> ChildInfo:
        """Get basic information about a child.

        Args:
            key: Child key to inspect.

        Returns:
            ChildInfo: Basic child information (exists, type, value).

        Note:
            Does NOT validate container health - pure data gathering.
            Use other methods for operations that require validation.
        """
        tx = self.get_ensured_transaction()

        child_path = self.path.join(key)
        child_struct_path = child_path.struct_path

        # Check if it's a container
        try:
            tx.get(child_struct_path.to_tuple())
            return ChildInfo(key=key, exists=True, child_type=ChildType.CONTAINER)
        except StorageKeyError:
            pass

        # Check if it's a primitive
        try:
            primitive_data = tx.get(child_path.to_tuple())
            return ChildInfo(
                key=key,
                exists=True,
                child_type=ChildType.PRIMITIVE,
                value=primitive_data,
            )
        except StorageKeyError:
            pass

        # Child doesn't exist
        return ChildInfo(key=key, exists=False, child_type=ChildType.NOT_FOUND)

    # ------------------------------------------------------------------------
    # VALIDATION LAYER - Child-Specific Validations
    # ------------------------------------------------------------------------

    def validate_child_key_available(
        self, key: PathComponent, /, *, child_info: ChildInfo | None = None
    ) -> None:
        """Validate that key is available for new primitive child.

        Args:
            key: Child key to check.
            container_info: Container info from get_info().

        Raises:
            PathExistsError: If child already exists (primitive or container).

        Note:
            This prevents creating primitive over existing container or vice versa.
        """
        child_info = child_info or self.get_child_info(key)
        if child_info.exists:
            raise PathExistsError(
                f"Child '{key}' already exists as {child_info.child_type.name.lower()}"
            )

    def validate_child_exists(
        self, key: PathComponent, /, *, child_info: ChildInfo | None = None
    ) -> None:
        """Validate that child exists.

        Args:
            key: Child key.
            child_info: Child info from get_child_info().

        Raises:
            PathNotFoundError: If child does not exist.
        """
        child_info = child_info or self.get_child_info(key)
        if not child_info.exists:
            raise PathNotFoundError(f"Child '{key}' does not exist")

    def validate_child_primitive(
        self, key: PathComponent, /, *, child_info: ChildInfo | None = None
    ) -> None:
        """Validate that child is primitive type.

        Args:
            key: Child key.
            child_info: Child info from get_child_info().

        Raises:
            PathNotFoundError: If child does not exist.
            PathTypeError: If child exists but is container.
        """
        child_info = child_info or self.get_child_info(key)

        self.validate_child_exists(key, child_info=child_info)

        if child_info.child_type != ChildType.PRIMITIVE:
            raise PathTypeError(
                f"Child '{key}' is {child_info.child_type.name.lower()}, not primitive"
            )

    def validate_child_container(
        self, key: PathComponent, /, *, child_info: ChildInfo | None = None
    ) -> None:
        """Validate that child is container type.

        Args:
            key: Child key.
            child_info: Child info from get_child_info().

        Raises:
            PathNotFoundError: If child does not exist.
            PathTypeError: If child exists but is primitive.
        """
        child_info = child_info or self.get_child_info(key)

        self.validate_child_exists(key, child_info=child_info)

        if child_info.child_type != ChildType.CONTAINER:
            raise PathTypeError(
                f"Child '{key}' is {child_info.child_type.name.lower()}, not container"
            )

    # ------------------------------------------------------------------------
    # EXECUTION LAYER - Operations with Health Checks
    # ------------------------------------------------------------------------

    def has_child(self, key: PathComponent, /, *, child_info: ChildInfo | None = None) -> bool:
        """Check if child exists with health checking.

        Args:
            key: Child key to check.

        Returns:
            bool: True if child exists (primitive or container).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
        """
        child_info = child_info or self.get_child_info(key)
        return child_info.exists

    def get_child_type(
        self, key: PathComponent, /, *, child_info: ChildInfo | None = None
    ) -> ChildType:
        """Get child type with health checking.

        Args:
            key: Child key to check.

        Returns:
            ChildType: Type of child (PRIMITIVE, CONTAINER, NOT_FOUND).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
        """
        child_info = child_info or self.get_child_info(key)
        return child_info.child_type

    def remove_child(self, key: PathComponent, /, *, child_info: ChildInfo | None = None) -> bool:
        """Remove child (primitive or container) with full validation.

        Args:
            key: Child key to remove.

        Returns:
            bool: True if removed, False if didn't exist.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.

        Process:
            1. Handle non-existent child (return False)
            3. Remove child (primitive or container)
        """
        child_info = child_info or self.get_child_info(key)

        # 1. Handle non-existent child
        if not child_info.exists:
            return False

        # 2. Remove child
        tx = self.get_ensured_transaction()
        child_path = self.path.join(key)

        if child_info.child_type == ChildType.CONTAINER:
            self._delete_subtree(child_path)
        else:
            tx.delete(child_path.to_tuple())

        return True

    def keys(self, *, primitives_only: bool = False) -> Generator[str, None, None]:
        """Get child keys with health checking.

        Args:
            primitives_only: If True, only return primitive child keys.

        Returns:
            tuple[str, ...]: Child keys.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
        """
        yield from self._get_keys_impl(primitives_only=primitives_only)

    def clear(self) -> int:
        """Remove all children with health checking.

        Returns:
            int: Number of children removed.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.
        """
        # Health check done by keys() and remove_child()
        child_keys = self.keys()
        removed_count = 0

        for key in child_keys:
            if self.remove_child(key):
                removed_count += 1

        return removed_count

    def children(self, *, primitives_only: bool = False) -> Generator[ChildInfo, None, None]:
        """Get child information with health checking.

        Args:
            primitives_only: If True, only return primitive children.

        Yields:
            ChildInfo: Information about each child (exists, type, value).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
        """
        for key in self._get_keys_impl(primitives_only=primitives_only):
            yield self.get_child_info(key)

    def get_primitive_value(
        self,
        key: PathComponent,
        /,
        *,
        child_info: ChildInfo | None = None,
        default: Value | Empty = EMPTY,
    ) -> Value | Empty:
        """Get primitive child value with full health checking.

        Args:
            key: Child key.
            default: Default value if child doesn't exist.

        Returns:
            Any: Primitive value or default.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible or child is container.
            ContainerProtocolError: If container malformed.

        Process:
            1. Handle non-existent child (return default)
            2. Validate child type (must be primitive)
            3. Return value
        """
        child_info = child_info or self.get_child_info(key)

        # 1. Handle non-existent child
        if not child_info.exists:
            return default

        # 2. Validate child type
        self.validate_child_primitive(key, child_info=child_info)

        # 3. Return value
        return child_info.value

    def set_primitive_value(
        self, key: PathComponent, value: Value, /, *, child_info: ChildInfo | None = None
    ) -> bool:
        """Set primitive child value with full validation.

        Args:
            key: Child key.
            value: Primitive value to set.

        Returns:
            bool: True if value was set, False if already existed with same value.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.
            PathExistsError: If child exists as container.

        Process:
            1. Validate operation (exists + compatible + primitive)
            2. Set value in transaction
        """
        child_info = child_info or self.get_child_info(key)

        # 1. Validate operation
        if child_info.exists:
            self.validate_child_primitive(key, child_info=child_info)
            # Check if value already correct
            if child_info.value == value:
                return False
        else:
            self.validate_child_key_available(key, child_info=child_info)

        # 2. Set value
        tx = self.get_ensured_transaction()
        child_path = self.path.join(key)
        tx.set(child_path.to_tuple(), value)

        return True

    # ------------------------------------------------------------------------
    # IMPLEMENTATION HELPERS
    # ------------------------------------------------------------------------

    def _get_keys_impl(self, primitives_only: bool = False) -> Generator[str, None, None]:
        """Implementation for key listing.

        Args:
            primitives_only: If True, only yield primitive keys.

        Yields:
            str: Child keys.
        """
        tx = self.get_ensured_transaction()

        # Get primitive keys
        try:
            for path_tuple in tx.list_keys(self.path.to_tuple(), depth=1):
                yield path_tuple[-1]  # Get last component (key)
        except StorageKeyError:
            pass  # Container might be empty

        # Get container keys if requested
        if not primitives_only:
            try:
                struct_path = self.path.struct_path
                for path_tuple in tx.list_keys(struct_path.to_tuple(), depth=1):
                    yield path_tuple[-1]  # Get last component (key)
            except StorageKeyError:
                pass  # No container children

    def _delete_subtree(self, path: Path) -> None:
        """
        Recursively delete a container and all its descendants.

        Args:
            path: Root path to delete
            tx: Transaction to use
        """
        tx = self.get_ensured_transaction()

        # Collect all paths
        paths_to_delete: list[PathTuple] = []
        paths_to_delete.extend([p for p in tx.list_keys(path.to_tuple(), depth=-1)])
        paths_to_delete.extend([p for p in tx.list_keys(path.struct_path.to_tuple(), depth=-1)])
        paths_to_delete.extend([p for p in tx.list_keys(path.meta_path.to_tuple(), depth=-1)])
        paths_to_delete.extend(
            [
                self.path.to_tuple(),
                self.path.struct_path.to_tuple(),
                self.path.meta_path.to_tuple(),
            ]
        )

        for path_to_delete in paths_to_delete:
            try:
                tx.delete(path_to_delete)
            except StorageKeyError:
                pass

    # =========================================================================
    # Metadata Operations
    # =========================================================================

    def get_metadata(self, key: PathComponent, default: Value | Empty = EMPTY) -> Value | Empty:
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

        metadata_path = self.path.struct_path.join(key)
        try:
            return tx.get(metadata_path.to_tuple())
        except StorageKeyError:
            return default

    def set_metadata(self, key: PathComponent, value: Value) -> None:
        """
        Set metadata value (e.g., __length__ for ListView).

        Args:
            key: Metadata key
            value: Metadata value to store
        """
        tx = self.get_ensured_transaction()
        metadata_path = self.path.struct_path.join(key)
        tx.set(metadata_path.to_tuple(), value)

    def has_metadata(self, key: PathComponent) -> bool:
        """
        Check if metadata key exists.

        Args:
            key: Metadata key to check

        Returns:
            bool: True if metadata exists
        """
        tx = self.get_ensured_transaction()
        metadata_path = self.path.struct_path.join(key)
        return tx.exists(metadata_path.to_tuple())

    def delete_metadata(self, key: PathComponent) -> None:
        """
        Delete metadata key.

        Args:
            key: Metadata key to delete
        """
        tx = self.get_ensured_transaction()
        metadata_path = self.path.struct_path.join(key)
        try:
            tx.delete(metadata_path.to_tuple())
        except StorageKeyError:
            pass
