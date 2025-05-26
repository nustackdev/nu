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

from ..backend import BackendProtocol, TransactionProtocol
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
        info: ContainerInfo object containing raw data about the container.
        tx: Transaction object for storage operations (must be provided, otherwise ValueError is raised).
        backend: Backend instance for low-level storage operations.
    """

    structure: ContainerStructure = attrs.field(kw_only=True)

    protocol: ContainerProtocol = attrs.field(kw_only=True)

    info: ContainerInfo = attrs.field(kw_only=True, eq=False, hash=False)

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

    @classmethod
    def create(
        cls,
        backend: BackendProtocol,
        tx: TransactionProtocol,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
        path: Path,
    ) -> ContainerNode:
        """
        Create a new ContainerNode instance with the given parameters.

        This method initializes a ContainerNode with the specified backend,
        transaction, structure, protocol, and path. It gathers raw information
        about the container and its parent chain without performing any validation
        logic. The gathered information is stored in the `info` attribute.

        Args:
            backend (BackendProtocol): The backend instance for storage operations.
            tx (TransactionProtocol): The transaction object for storage operations.
            structure (ContainerStructure): The expected structure type of the container.
            protocol (ContainerProtocol): The expected protocol flags for the container.
            path (Path): The path to the container in the state tree.

        Returns:
            ContainerNode: A new instance of ContainerNode initialized with the provided parameters.
        """
        info = cls.get_info(path, tx)

        return cls(
            backend=backend,
            tx=tx,
            path=path,
            structure=structure,
            protocol=protocol,
            info=info,
        )

    @classmethod
    def get_info(cls, path: Path, tx: TransactionProtocol, /) -> ContainerInfo:
        """Gather raw information about container and parent chain.

        This method performs pure data collection without making any validation
        decisions. It touches all relevant storage keys to ensure proper transaction
        read-locking and gathers comprehensive information about the container
        and its entire parent chain.

        The method traverses the path hierarchy from root to target, collecting
        raw storage data and categorizing paths based on existence and data format,
        but does not perform any validation logic or make decisions about whether
        the data is "valid" or "invalid" - that's left to validation methods.

        Args:
            path: The path to gather information about.
            tx: The transaction object for storage operations.

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
        paths_to_check = cls._get_path_chain(path)

        # Gather parent information
        parent_infos = []
        missing_paths = []
        malformed_paths = []

        # Check all parents (excluding target)
        for path in paths_to_check[:-1]:
            parent_info = cls._get_path_info(path, tx)
            parent_infos.append(parent_info)

            if not parent_info.exists:
                missing_paths.append(path)
            elif parent_info.stored_structure is None or parent_info.stored_protocol is None:
                # Malformed data
                malformed_paths.append(path)

        # Check target container
        target_path = paths_to_check[-1]
        target_info = cls._get_path_info(target_path, tx)

        return ContainerInfo(
            exists=target_info.exists,
            stored_structure=target_info.stored_structure,
            stored_protocol=target_info.stored_protocol,
            raw_type_data=target_info.raw_type_data,
            parents=tuple(parent_infos),
            missing_parent_paths=tuple(missing_paths),
            malformed_parent_paths=tuple(malformed_paths),
        )

    @classmethod
    def _get_path_chain(cls, path: Path, /) -> list[Path]:
        """Get complete path chain from root to target container.

        Traverses from the target path up to the root, collecting all intermediate
        paths, then reverses the list to provide root-to-target ordering.

        Args:
            path: The path to process.

        Returns:
            list[Path]: Ordered list of paths from root to target, including
                the target path itself. Empty list if path has no parents.

        Example:
            For path '/a/b/c', returns [Path(), Path('a'), Path('a', 'b'), Path('a', 'b', 'c')]
        """
        paths = []
        current = path
        while current is not None:
            paths.append(current)
            current = current.parent()
        return list(reversed(paths))

    @classmethod
    def _get_path_info(cls, path: Path, tx: TransactionProtocol, /) -> ParentInfo:
        """Get raw storage information for a single path.

        Retrieves raw type metadata from storage and attempts to parse it into
        structure and protocol enums. Does not validate compatibility or
        correctness - just extracts what's available.

        Args:
            path: The path to gather information about.
            tx: The transaction object for storage operations.

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

    def validate_exists(self) -> None:
        """Validate that the container exists in storage.

        Raises:
            PathNotFoundError: If the container does not exist.

        Example:
            ```python
            container.validate_exists()  # Raises if not found
            ```
        """
        if not self.info.exists:
            raise PathNotFoundError(f"Container at {self.path} does not exist")

    def validate_not_exists(self) -> None:
        """Validate that the container does not exist in storage.

        Useful for create operations where the container should not already exist.

        Raises:
            PathExistsError: If the container already exists.

        Example:
            ```python
            container.validate_not_exists()  # Raises if exists
            ```
        """
        if self.info.exists:
            raise PathExistsError(f"Container at {self.path} already exists")

    def validate_compatible(self) -> None:
        """Validate that the container type is compatible with expected structure/protocol.

        Checks that the container exists, has well-formed type data, and that
        both structure and protocol are compatible with this node's expectations.
        Structure compatibility uses bitwise AND to allow subset matching.
        Protocol compatibility requires at least one common flag.

        Raises:
            PathNotFoundError: If the container does not exist.
            PathTypeError: If type data is malformed or incompatible.

        Example:
            ```python
            container.validate_compatible()  # Raises if incompatible
            ```
        """
        self.validate_exists()

        if self.info.stored_structure is None or self.info.stored_protocol is None:
            raise PathTypeError(
                f"Container at {self.path} has malformed type data: {self.info.raw_type_data}"
            )

        structure_match = self.structure & self.info.stored_structure == self.structure
        protocol_match = bool(self.protocol & self.info.stored_protocol)

        if not structure_match:
            raise PathTypeError(
                f"Structure mismatch at {self.path}: "
                f"expected {self.structure}, got {self.info.stored_structure}"
            )

        if not protocol_match:
            raise PathTypeError(
                f"Protocol mismatch at {self.path}: "
                f"expected {self.protocol}, got {self.info.stored_protocol}"
            )

    def validate_parents_exist(self) -> None:
        """Validate that all parent containers exist in storage.

        Raises:
            PathNotFoundError: If any parent containers are missing.

        Example:
            ```python
            container.validate_parents_exist()  # Raises if parents missing
            ```
        """
        if self.info.missing_parent_paths:
            raise PathNotFoundError(f"Missing parent containers: {self.info.missing_parent_paths}")

    def validate_parents_healthy(self) -> None:
        """Validate that all parent containers have well-formed type data.

        Checks that existing parent containers have parseable structure and
        protocol information. Does not validate compatibility - only that
        the data format is correct.

        Raises:
            PathTypeError: If any parent containers have malformed type data.

        Example:
            ```python
            container.validate_parents_healthy()  # Raises if data corrupted
            ```
        """
        if self.info.malformed_parent_paths:
            raise PathTypeError(f"Malformed parent containers: {self.info.malformed_parent_paths}")

    def validate_parents_chain(self) -> None:
        """Validate that the entire parent chain is valid and complete.

        Combines existence and health checks to ensure all parents exist
        and have well-formed type data. This is the comprehensive parent
        validation used when parent creation is not allowed.

        Raises:
            PathNotFoundError: If any parent containers are missing.
            PathTypeError: If any parent containers have malformed type data.

        Example:
            ```python
            container.validate_parents_chain()  # Full parent validation
            ```
        """
        self.validate_parents_exist()
        self.validate_parents_healthy()

    def validate_mutable(self) -> None:
        """Validate that the container supports mutation operations.

        Checks that the container exists, is compatible with expected type,
        and has the MUTABLE protocol flag set. Required before any mutation
        operations like adding or removing children.

        Raises:
            PathNotFoundError: If container does not exist.
            PathTypeError: If container is incompatible or has malformed data.
            ContainerProtocolError: If container is not mutable.

        Example:
            ```python
            container.validate_mutable()  # Raises if cannot mutate
            ```
        """
        self.validate_compatible()

        if self.info.stored_protocol is None:
            raise PathTypeError(
                f"Container at {self.path} has malformed protocol data. Can not check mutability."
            )

        if ~(self.info.stored_protocol & ContainerProtocol.MUTABLE):
            raise ContainerProtocolError(f"Container at {self.path} is not mutable")

    def validate_createable(self, *, parents: bool = True) -> None:
        """Validate that container creation is possible.

        Checks conditions required for successful container creation, including
        non-existence of the target and parent chain requirements based on
        whether parent creation is allowed.
        Validates parent mutability when creating in existing parent.

        Args:
            parents: Whether parent creation is allowed. If True, only malformed
                parents block creation. If False, complete parent chain required.

        Raises:
            PathExistsError: If container already exists.
            PathTypeError: If malformed parents prevent creation.
            PathNotFoundError: If parents=False and parents are missing.
            ContainerProtocolError: If parent is not mutable.

        Example:
            ```python
            container.validate_createable(parents=True)  # Allow parent creation
            container.validate_createable(parents=False)  # Require existing parents
            ```
        """
        if self.info.exists:
            raise PathExistsError(f"Container at {self.path} already exists")

        if parents:
            # With parent creation, only malformed parents block creation
            self.validate_parents_healthy()
        else:
            # Without parent creation, need complete valid chain
            self.validate_parents_chain()

        # Validate parent is mutable
        self.validate_parent_mutable()

    def validate_parents_createable(self) -> None:
        """Validate that missing parent containers can be created.

        Checks that there are no malformed parents that would prevent creation
        of missing parents. Malformed parents cannot be automatically fixed
        and must be resolved manually.

        Raises:
            PathTypeError: If malformed parents prevent creation.

        Example:
            ```python
            container.validate_parents_createable()  # Check if can create parents
            ```
        """
        # Only malformed parents prevent creation
        self.validate_parents_healthy()

    def validate_parent_mutable(self) -> None:
        """Validate that the immediate parent container is mutable.

        Used when creating a new container to ensure the parent can accept
        new children. Only checks the immediate parent, not the entire chain.

        Raises:
            PathNotFoundError: If immediate parent does not exist.
            PathTypeError: If parent has malformed data.
            ContainerProtocolError: If parent is not mutable.

        Example:
            ```python
            container.validate_parent_mutable()  # Check parent can accept children
            ```
        """
        if not self.info.parents:
            # No parents - root level creation always allowed
            return

        first_existing_parent_mutable = True
        parent_info = None
        for parent_info in self.info.parents[-1::-1]:  # Iterate from immediate parent to root
            if parent_info.exists:
                if parent_info.stored_protocol is None:
                    raise PathTypeError(
                        f"Parent container at {parent_info.path} has malformed protocol data. Can not check mutability."
                    )
                first_existing_parent_mutable = bool(
                    parent_info.stored_protocol & ContainerProtocol.MUTABLE
                )
                break

        if parent_info is None:
            return  # No parents at all, 0 level - always mutable

        if not first_existing_parent_mutable:
            raise ContainerProtocolError(f"Parent container at {parent_info.path} is not mutable")

    # ------------------------------------------------------------------------
    # SUPPORT LAYER - Boolean Feasibility Checks
    # ------------------------------------------------------------------------

    def supports_creation(self, *, parents: bool = True) -> bool:
        """Check if container creation is feasible without raising exceptions.

        Wrapper around validate_createable() that returns a boolean result
        instead of raising exceptions. Useful for conditional logic where
        you want to check feasibility before attempting creation.

        Args:
            parents: Whether parent creation should be considered feasible.

        Returns:
            bool: True if try_create() would succeed, False otherwise.

        Example:
            ```python
            if container.supports_creation():
                result = container.try_create()  # Guaranteed to succeed
            else:
                handle_creation_blocked()
            ```
        """
        try:
            self.validate_createable(parents=parents)
            return True
        except (PathExistsError, PathTypeError, ContainerProtocolError):
            return False

    def supports_mutation(self) -> bool:
        """Check if container mutation is feasible without raising exceptions.

        Wrapper around validate_mutable() that returns a boolean result.
        Useful for determining if mutation operations like add/remove children
        would be successful.

        Returns:
            bool: True if mutation operations would succeed, False otherwise.

        Example:
            ```python
            if container.supports_mutation():
                # Safe to perform mutations
                container.add_child(key, value)
            ```
        """
        try:
            self.validate_mutable()
            return True
        except (PathNotFoundError, PathTypeError, ContainerProtocolError):
            return False

    def supports_compatibility(self) -> bool:
        """Check if container is compatible with expected type without raising exceptions.

        Wrapper around validate_compatible() that returns a boolean result.
        Useful for checking type compatibility in conditional logic.

        Returns:
            bool: True if container matches expected structure/protocol, False otherwise.

        Example:
            ```python
            if container.supports_compatibility():
                # Container matches expected type
                proceed_with_operations()
            else:
                handle_type_mismatch()
            ```
        """
        try:
            self.validate_compatible()
            return True
        except (PathNotFoundError, PathTypeError, ContainerProtocolError):
            return False

    # ------------------------------------------------------------------------
    # EXECUTION LAYER - Performs Operations
    # ------------------------------------------------------------------------

    def try_create(self, *, parents: bool = True) -> bool:
        """Create the container if it doesn't exist.

        Attempts to create the container after validating that creation is
        possible. If the container already exists with compatible type,
        returns False without error. Creates missing parents if requested
        and needed.

        Args:
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
            try:
                created = container.try_create(parents=True)
                if created:
                    print("Container created successfully")
                else:
                    print("Container already existed")
            except PathTypeError as e:
                print(f"Type conflict: {e}")
            ```
        """
        # Handle already exists case
        if self.info.exists:
            if self.supports_compatibility():
                return False  # Already exists with compatible type
            else:
                # Exists but incompatible - validate will raise appropriate error
                self.validate_compatible()

        # Validate we can create
        self.validate_createable(parents=parents)

        # Create parents if needed
        if parents and self.info.missing_parent_paths:
            self.try_create_parents()

        # Create container
        self.tx.set(self.path.struct_path.to_tuple(), [self.structure.value, self.protocol.value])

        return True

    def try_create_parents(self) -> list[Path]:
        """Create missing parent containers.

        Creates any missing parent containers using default MAPPING_CONTAINER
        structure and DICT protocol. Only creates parents that are actually
        missing - existing parents are left unchanged.

        Returns:
            list[Path]: List of parent paths that were actually created.
                Empty list if no parents needed creation.

        Raises:
            PathTypeError: If malformed parent data prevents creation.

        Example:
            ```python
            try:
                created = container.try_create_parents()
                print(f"Created {len(created)} parent containers")
            except PathTypeError as e:
                print(f"Cannot create parents: {e}")
            ```

        Note:
            Created parents use MAPPING_CONTAINER|DICT which provides
            maximum compatibility for child container creation.
        """
        self.validate_parents_createable()

        if not self.info.missing_parent_paths:
            return []

        created = []

        for parent_path in self.info.missing_parent_paths:
            self.tx.set(
                parent_path.struct_path.to_tuple(),
                [ContainerStructure.MAPPING_CONTAINER.value, ContainerProtocol.DICT.value],
            )
            created.append(parent_path)

        return created

    # ------------------------------------------------------------------------
    # CONVENIENCE LAYER - Common Operation Patterns
    # ------------------------------------------------------------------------

    def ensure_exists(self, *, parents: bool = True) -> bool:
        """Ensure container exists, creating if necessary or validating if present.

        High-level convenience method that handles both creation and validation
        scenarios. If container exists, validates compatibility. If missing,
        creates it with optional parent creation.

        Args:
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
            created = container.ensure_exists(parents=True)
            # Now guaranteed: container exists and is compatible
            ```
        """
        if self.info.exists:
            self.validate_compatible()
            return False
        else:
            return self.try_create(parents=parents)

    def ensure_parents(self) -> list[Path]:
        """Ensure all parent containers exist, creating missing ones.

        Convenience method that ensures the entire parent chain is healthy
        and complete. Creates any missing parents and validates that existing
        parents have well-formed data.

        Returns:
            list[Path]: List of parent paths that were created. Empty if
                all parents already existed.

        Raises:
            PathTypeError: If existing parents have malformed data that
                cannot be automatically resolved.

        Example:
            ```python
            created = container.ensure_parents()
            # Now guaranteed: all parents exist and are healthy
            ```
        """
        if not self.info.missing_parent_paths:
            self.validate_parents_healthy()  # Ensure existing parents are healthy
            return []

        return self.try_create_parents()

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
        child_path = self.path.join(key)
        child_struct_path = child_path.struct_path

        # Check if it's a primitive
        # Note: First checking primitive to avoid unnecessary container checks,
        # as primitives are more common and faster to access.
        try:
            primitive_data = self.tx.get(child_path.to_tuple())
            return ChildInfo(
                key=key,
                exists=True,
                child_type=ChildType.PRIMITIVE,
                value=primitive_data,
            )
        except StorageKeyError:
            pass

        # Check if it's a container
        try:
            self.tx.get(child_struct_path.to_tuple())
            return ChildInfo(key=key, exists=True, child_type=ChildType.CONTAINER)
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
            child_info: Child info from get_child_info().

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
        """Check if child exists with container health validation.

        Args:
            key: Child key to check.
            child_info: Optional child info from get_child_info().

        Returns:
            bool: True if child exists (primitive or container).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.

        Example:
            ```python
            if container.has_child("key"):
                print("Child exists")
            ```
        """
        child_info = child_info or self.get_child_info(key)
        return child_info.exists

    def get_child_type(
        self, key: PathComponent, /, *, child_info: ChildInfo | None = None
    ) -> ChildType:
        """Get child type with container health validation.

        Args:
            key: Child key to check.
            child_info: Optional child info from get_child_info().

        Returns:
            ChildType: Type of child (PRIMITIVE, CONTAINER, NOT_FOUND).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.

        Example:
            ```python
            child_type = container.get_child_type("key")
            if child_type == ChildType.PRIMITIVE:
                print("It's a primitive value")
            ```
        """
        child_info = child_info or self.get_child_info(key)
        return child_info.child_type

    def remove_child(self, key: PathComponent, /, *, child_info: ChildInfo | None = None) -> bool:
        """Remove child (primitive or container) with mutability validation.

        Args:
            key: Child key to remove.
            child_info: Optional child info from get_child_info().

        Returns:
            bool: True if removed, False if didn't exist.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.

        Example:
            ```python
            if container.remove_child("key"):
                print("Child removed")
            else:
                print("Child didn't exist")
            ```
        """
        # Validate container is mutable
        self.validate_mutable()

        child_info = child_info or self.get_child_info(key)

        # Handle non-existent child
        if not child_info.exists:
            return False

        # Remove child
        child_path = self.path.join(key)

        if child_info.child_type == ChildType.CONTAINER:
            self._delete_subtree(child_path)
        else:
            self.tx.delete(child_path.to_tuple())

        return True

    def keys(self, *, primitives_only: bool = False) -> Generator[PathComponent, None, None]:
        """Get child keys with container health validation.

        Args:
            primitives_only: If True, only return primitive child keys.

        Yields:
            PathComponent: Child keys.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.

        Example:
            ```python
            for key in container.keys():
                print(f"Child: {key}")
            ```
        """
        # Validate container health first
        self.validate_compatible()

        yield from self._get_keys_impl(primitives_only=primitives_only)

    def clear(self) -> int:
        """Remove all children with mutability validation.

        Returns:
            int: Number of children removed.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.

        Example:
            ```python
            removed_count = container.clear()
            print(f"Removed {removed_count} children")
            ```
        """
        # Validate container is mutable
        self.validate_mutable()

        removed_count = 0

        for key in self.keys():
            if self.remove_child(key):
                removed_count += 1

        return removed_count

    def children(self, *, primitives_only: bool = False) -> Generator[ChildInfo, None, None]:
        """Get child information with container health validation.

        Args:
            primitives_only: If True, only return primitive children.

        Yields:
            ChildInfo: Information about each child (exists, type, value).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.

        Example:
            ```python
            for child in container.children():
                print(f"Child {child.key}: {child.child_type}")
            ```
        """
        # Validate container health first
        self.validate_compatible()

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
            child_info: Optional child info from get_child_info().
            default: Default value if child doesn't exist.

        Returns:
            Value | Empty: Primitive value or default.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible or child is container.
            ContainerProtocolError: If container malformed.

        Example:
            ```python
            value = container.get_primitive_value("key", default="not found")
            print(f"Value: {value}")
            ```
        """
        # Validate container health
        self.validate_compatible()

        child_info = child_info or self.get_child_info(key)

        # Handle non-existent child
        if not child_info.exists:
            return default

        # Validate child type
        self.validate_child_primitive(key, child_info=child_info)

        # Return value
        return child_info.value

    def set_primitive_value(
        self, key: PathComponent, value: Value, /, *, child_info: ChildInfo | None = None
    ) -> bool:
        """Set primitive child value with mutability validation.

        Args:
            key: Child key.
            value: Primitive value to set.
            child_info: Optional child info from get_child_info().

        Returns:
            bool: True if value was set, False if already existed with same value.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.
            PathExistsError: If child exists as container.

        Example:
            ```python
            if container.set_primitive_value("key", "value"):
                print("Value set")
            else:
                print("Value was already correct")
            ```
        """
        # Validate container is mutable
        self.validate_mutable()

        child_info = child_info or self.get_child_info(key)

        # Validate operation
        if child_info.exists:
            self.validate_child_primitive(key, child_info=child_info)
            # Check if value already correct
            if child_info.value == value:
                return False
        else:
            self.validate_child_key_available(key, child_info=child_info)

        # Set value
        child_path = self.path.join(key)
        self.tx.set(child_path.to_tuple(), value)

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
        # Get primitive keys
        try:
            for path_tuple in self.tx.list_keys(self.path.to_tuple(), depth=1):
                yield path_tuple[-1]  # Get last component (key)
        except StorageKeyError:
            pass  # Container might be empty

        # Get container keys if requested
        if not primitives_only:
            try:
                struct_path = self.path.struct_path
                for path_tuple in self.tx.list_keys(struct_path.to_tuple(), depth=1):
                    yield path_tuple[-1]  # Get last component (key)
            except StorageKeyError:
                pass  # No container children

    def _delete_subtree(self, path: Path) -> None:
        """
        Recursively delete a container and all its descendants.

        Args:
            path: Root path to delete
        """
        # Collect all paths
        paths_to_delete: list[PathTuple] = []
        paths_to_delete.extend([p for p in self.tx.list_keys(path.to_tuple(), depth=-1)])
        paths_to_delete.extend(
            [p for p in self.tx.list_keys(path.struct_path.to_tuple(), depth=-1)]
        )
        paths_to_delete.extend([p for p in self.tx.list_keys(path.meta_path.to_tuple(), depth=-1)])
        paths_to_delete.extend(
            [
                self.path.to_tuple(),
                self.path.struct_path.to_tuple(),
                self.path.meta_path.to_tuple(),
            ]
        )

        for path_to_delete in paths_to_delete:
            try:
                self.tx.delete(path_to_delete)
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

        Example:
            ```python
            length = container.get_metadata("__length__", 0)
            ```
        """
        metadata_path = self.path.struct_path.join(key)
        try:
            return self.tx.get(metadata_path.to_tuple())
        except StorageKeyError:
            return default

    def set_metadata(self, key: PathComponent, value: Value) -> None:
        """
        Set metadata value (e.g., __length__ for ListView).

        Args:
            key: Metadata key
            value: Metadata value to store

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.

        Example:
            ```python
            container.set_metadata("__length__", 10)
            ```
        """
        # Validate container is mutable
        self.validate_mutable()

        metadata_path = self.path.struct_path.join(key)
        self.tx.set(metadata_path.to_tuple(), value)

    def has_metadata(self, key: PathComponent) -> bool:
        """
        Check if metadata key exists.

        Args:
            key: Metadata key to check

        Returns:
            bool: True if metadata exists

        Example:
            ```python
            if container.has_metadata("__length__"):
                print("Container has length metadata")
            ```
        """
        metadata_path = self.path.struct_path.join(key)
        return self.tx.exists(metadata_path.to_tuple())

    def delete_metadata(self, key: PathComponent) -> None:
        """
        Delete metadata key.

        Args:
            key: Metadata key to delete

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.

        Example:
            ```python
            container.delete_metadata("__length__")
            ```
        """
        # Validate container is mutable
        self.validate_mutable()

        metadata_path = self.path.struct_path.join(key)
        try:
            self.tx.delete(metadata_path.to_tuple())
        except StorageKeyError:
            pass
