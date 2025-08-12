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
@lru_cache can't be used directly to avoid the need of manual cache invalidation due to
strong references to the cached arguments, including `self`, which prevents
the instance from being garbage collected.
So:
- We use @cached_property to cache non-argument methods (like validation checks).
- TODO: A separate cache service to be added for more complex operations that have arguments.

**Operation Tracking & Conflict Detection**
The transaction system records all read operations through "get_for_update" tracking.
When methods like exists() or validate_parents_exist() access data, the transaction
logs these keys for optimistic concurrency control. If concurrent transactions touch
overlapping data, the system detects conflicts and handles them through retries or
explicit resolution.

**Container Type Marking**
Container types are stored using special markers at the data path to distinguish them
from primitive values. The marker format includes both structure and protocol information
embedded in the value itself, eliminating the need for separate storage namespaces.

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
from functools import cached_property
from typing import ClassVar, Generator

import attrs

from ...backend import ObservableStorage, StorageKeyError
from ..context.protocols import ContextType
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
    stored_structure: ContainerStructure | None = None  # For containers
    stored_protocol: ContainerProtocol | None = None  # For containers


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

    # Container type marker for distinguishing containers from primitives
    _CONTAINER_MARKER: ClassVar[str] = "\ue000"
    # The Private Use Area (PUA) is a range of Unicode code points (U+E000 to U+F8FF)
    # that are intentionally not assigned to any standard characters.
    # Using PUA characters virtually eliminates the risk of collision since:
    # - They don't appear on standard keyboards
    # - They're not used in any human writing systems
    # - They have no standard visual representation

    structure: ContainerStructure = attrs.field(kw_only=True)

    protocol: ContainerProtocol = attrs.field(kw_only=True)

    info: ContainerInfo = attrs.field(kw_only=True, eq=False, hash=False)

    @cached_property
    def node_type(self) -> NodeType:
        """Get the type of this node.

        Returns:
            NodeType: Always returns NodeType.CONTAINER for container nodes.
        """
        return NodeType.CONTAINER

    # ========================================================================
    # CONTAINER OPERATIONS
    # ========================================================================

    # ------------------------------------------------------------------------
    # HELPER STATIC METHODS (typically used internally)
    # ------------------------------------------------------------------------

    @staticmethod
    def extract_type_info(type_data: Value) -> tuple[ContainerStructure, ContainerProtocol]:
        """Extract structure and protocol from container marker data.

        Args:
            type_data: Raw marker data from storage, expected to be a string
                in format "\ue000[structure_value,protocol_value]".

        Returns:
            tuple[ContainerStructure, ContainerProtocol]: Parsed structure and protocol enums.

        Raises:
            ValueError: If type_data is malformed or cannot be parsed.
        """
        if not isinstance(type_data, str) or not type_data.startswith(
            ContainerNode._CONTAINER_MARKER
        ):
            raise ValueError(f"Malformed container marker: {type_data}")

        try:
            # Extract the bracketed content
            bracket_content = type_data[len(ContainerNode._CONTAINER_MARKER) :]
            if not (bracket_content.startswith("[") and bracket_content.endswith("]")):
                raise ValueError(f"Invalid marker format: {type_data}")

            # Parse the values inside brackets
            values_str = bracket_content[1:-1]  # Remove [ and ]
            values = values_str.split(",")
            if len(values) != 2:
                raise ValueError(f"Expected 2 values in marker: {type_data}")

            structure = ContainerStructure(int(values[0].strip()))
            protocol = ContainerProtocol(int(values[1].strip()))
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid container marker format: {type_data}") from e

        return structure, protocol

    @staticmethod
    def create_type_marker(structure: ContainerStructure, protocol: ContainerProtocol) -> str:
        """Create a container type marker string.

        Args:
            structure: Container structure type.
            protocol: Container protocol flags.

        Returns:
            str: Formatted marker string.
        """
        return f"{ContainerNode._CONTAINER_MARKER}[{structure},{protocol.value}]"

    # ------------------------------------------------------------------------
    # HIGH-LEVEL CONTAINER OPERATIONS
    # ------------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        backend: ObservableStorage,
        ctx: ContextType,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
        path: Path,
        ensure_exists: bool = True,
    ) -> ContainerNode:
        """
        Create a new ContainerNode instance with the given parameters.

        This method initializes a ContainerNode with the specified backend,
        transaction, structure, protocol, and path. It gathers raw information
        about the container and its parent chain without performing any validation
        logic. The gathered information is stored in the `info` attribute.

        Args:
            backend (BackendProtocol): The backend instance for storage operations.
            ctx (ContextType): The context object for storage operations (transaction or snapshot).
            structure (ContainerStructure): The expected structure type of the container.
            protocol (ContainerProtocol): The expected protocol flags for the container.
            path (Path): The path to the container in the state tree.

        Returns:
            ContainerNode: A new instance of ContainerNode initialized with the provided parameters.
        """
        if ensure_exists:
            info = cls.get_info(path, ctx)
            if not info.exists:
                container = cls(
                    backend=backend,
                    ctx=ctx,
                    path=path,
                    structure=structure,
                    protocol=protocol,
                    info=info,
                )
                container.ensure_exists()

        info = cls.get_info(path, ctx)
        return cls(
            backend=backend,
            ctx=ctx,
            path=path,
            structure=structure,
            protocol=protocol,
            info=info,
        )

    # ------------------------------------------------------------------------
    # INFORMATION LAYER - Pure Data Gathering (No Validation Logic)
    # ------------------------------------------------------------------------

    @classmethod
    def get_info(cls, path: Path, ctx: ContextType, /) -> ContainerInfo:
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
            ctx: The context object for storage operations.

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
            parent_info = cls._get_path_info(path, ctx)
            parent_infos.append(parent_info)

            if not parent_info.exists:
                missing_paths.append(path)
            elif parent_info.stored_structure is None or parent_info.stored_protocol is None:
                # Malformed data
                malformed_paths.append(path)

        # Check target container
        target_path = paths_to_check[-1]
        target_info = cls._get_path_info(target_path, ctx)

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
    def _get_path_info(cls, path: Path, ctx: ContextType, /) -> ParentInfo:
        """Get raw storage information for a single path.

        Retrieves raw data from storage and attempts to parse it as a container marker.
        Does not validate compatibility or correctness - just extracts what's available.

        Args:
            path: The path to gather information about.
            ctx: The context object for storage operations.

        Returns:
            ParentInfo: Raw information including:
                - Whether the path exists in storage
                - Parsed structure/protocol if data is a container marker
                - Raw storage data for malformed entries
                - None values for structure/protocol indicate non-container or malformed data

        Note:
            This method does not raise storage exceptions - missing keys result
            in exists=False, and malformed data results in None enum values.
        """
        try:
            raw_data = ctx.get(path.to_tuple())

            # Try to parse as container marker
            structure = None
            protocol = None
            try:
                structure, protocol = cls.extract_type_info(raw_data)
            except ValueError:
                pass  # Keep as None - indicates non-container or malformed data

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

    @cached_property
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

    @cached_property
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

    @cached_property
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
        self.validate_exists

        if self.info.stored_structure is None or self.info.stored_protocol is None:
            raise PathTypeError(
                f"Container at {self.path} has malformed type data: {self.info.raw_type_data}"
            )

        structure_match = self.info.stored_structure == self.structure
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

    @cached_property
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

    @cached_property
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

    @cached_property
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
        self.validate_parents_exist
        self.validate_parents_healthy

    @cached_property
    def validate_no_collision(self) -> None:
        """Validate that no primitive path collides with container path.

        This is important to avoid collisions where
        a container's path matches an existing primitive value.

        Raises:
            PathTypeError: If a collision is detected.

        Example:
            ```python
            container.validate_no_collision()  # Raises if path collides with primitive
            ```
        """
        if not self.info.parents:
            # No parents - root level, no collisions possible
            return

        # Check if the path exists and is not a container marker
        try:
            existing_data = self.get_ensured_context().get(self.path.to_tuple())
            # If we can extract type info, it's a container, which is fine
            try:
                self.extract_type_info(existing_data)
            except ValueError:
                # Not a container marker - this is a collision
                raise PathTypeError(
                    f"Path collision detected: {self.path} collides with an existing primitive value"
                )
        except StorageKeyError:
            # Path doesn't exist - no collision
            pass

    @cached_property
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

        # Validate that no primitive path collides with container path
        self.validate_no_collision

        if parents:
            # With parent creation, only malformed parents block creation
            self.validate_parents_healthy
        else:
            # Without parent creation, need complete valid chain
            self.validate_parents_chain

        # Validate parent is mutable
        self.validate_parent_mutable

    @cached_property
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
        self.validate_parents_healthy

    @cached_property
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
        self.validate_compatible

        if self.protocol is None:
            raise PathTypeError(
                f"Container at {self.path} has malformed protocol data. Can not check mutability."
            )

        if not (self.protocol & ContainerProtocol.MUTABLE):
            raise ContainerProtocolError(f"Container at {self.path} is not mutable")

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

    @cached_property
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
            self.validate_mutable
            return True
        except (PathNotFoundError, PathTypeError, ContainerProtocolError):
            return False

    @cached_property
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
            self.validate_compatible
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
            if self.supports_compatibility:
                return False  # Already exists with compatible type
            else:
                # Exists but incompatible - validate will raise appropriate error
                self.validate_compatible

        # Validate we can create
        self.validate_createable(parents=parents)

        # Create parents if needed
        if parents and self.info.missing_parent_paths:
            self.try_create_parents()

        # Create container
        marker = self.create_type_marker(self.structure, self.protocol)
        self.get_transaction_context().set(self.path.to_tuple(), marker)

        return True

    def try_create_parents(self) -> list[Path]:
        """Create missing parent containers.

        Creates any missing parent containers using default structure and protocol.
        Only creates parents that are actually missing - existing parents are left unchanged.

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
        self.validate_parents_createable

        if not self.info.missing_parent_paths:
            return []

        created = []

        for parent_path in self.info.missing_parent_paths:
            marker = self.create_type_marker(
                ContainerStructure(1),  # By default creates a dictionary-like container
                ContainerProtocol.DEFAULT_PROTOCOL,
            )
            self.get_transaction_context().set(parent_path.to_tuple(), marker)
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
            self.validate_compatible
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
            self.validate_parents_healthy  # Ensure existing parents are healthy
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

        try:
            child_data = self.get_ensured_context().get(child_path.to_tuple())

            # Try to parse as container marker
            try:
                child_structure, child_protocol = self.extract_type_info(child_data)
                return ChildInfo(
                    key=key,
                    exists=True,
                    child_type=ChildType.CONTAINER,
                    stored_structure=child_structure,
                    stored_protocol=child_protocol,
                )
            except ValueError:
                # Not a container marker - it's a primitive
                return ChildInfo(
                    key=key,
                    exists=True,
                    child_type=ChildType.PRIMITIVE,
                    value=child_data,
                )
        except StorageKeyError:
            # Child doesn't exist
            return ChildInfo(key=key, exists=False, child_type=ChildType.NOT_FOUND)

    # ------------------------------------------------------------------------
    # INSPECTION LAYER - Child Existance and Type Checks
    # ------------------------------------------------------------------------

    def has_primitive_child(self, key: PathComponent, /) -> bool:
        """Check if primitive child exists with container health validation.

        Args:
            key: Child key to check.

        Returns:
            bool: True if primitive child exists.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.

        Example:
            ```python
            if container.has_primitive_child("key"):
                print("Primitive child exists")
            ```
        """
        self.validate_compatible

        child_info = self.get_child_info(key)
        return child_info.child_type == ChildType.PRIMITIVE

    def has_container_child(self, key: PathComponent, /) -> bool:
        """Check if container child exists with container health validation.

        Args:
            key: Child key to check.

        Returns:
            bool: True if container child exists.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.

        Example:
            ```python
            if container.has_container_child("key"):
                print("Container child exists")
            ```
        """
        self.validate_compatible

        child_info = self.get_child_info(key)
        return child_info.child_type == ChildType.CONTAINER

    def has_child(self, key: PathComponent, /) -> ChildType:
        """Check if child exists with container health validation.

        Args:
            key: Child key to check.

        Returns:
            ChildType: Type of child (PRIMITIVE, CONTAINER, NOT_FOUND).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.

        Example:
            ```python
            child_type = container.has_child("key")
            if child_type == ChildType.PRIMITIVE:
                print("It's a primitive value")
            elif child_type == ChildType.CONTAINER:
                print("It's a container")
            else:
                print("Child does not exist")
            ```
        """
        self.validate_compatible

        return self.get_child_info(key).child_type

    # ------------------------------------------------------------------------
    # MANIPULATION LAYER - Add/Remove Children
    # ------------------------------------------------------------------------

    def set_primitive_child(self, key: PathComponent, value: Value, /) -> None:
        """Set primitive child value with mutability validation.

        Args:
            key: Child key to set.
            value: Primitive value to store.

        Returns:
            bool: True if value was set, False if already existed with same value.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container not mutable.
            PathExistsError: If child exists as container.

        Example:
            ```python
            if container.set_primitive_child("key", "value"):
                print("Value set")
            else:
                print("Value was already correct")
            ```
        """
        # Validate container is mutable
        self.validate_mutable

        # Validate primitive key is available (not a container)
        if self.has_container_child(key):
            raise PathExistsError(
                f"Child '{key}' already exists as a container. Cannot set primitive value."
            )

        self.get_transaction_context().set(self.path.join(key).to_tuple(), value)

    def remove_child(self, key: PathComponent, /) -> bool:
        """Remove child (primitive or container) with mutability validation.

        Args:
            key: Child key to remove.

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
        self.validate_mutable

        return self._delete_subtree(self.path.join(key))

    def clear_children(self) -> int:
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
        self.validate_mutable

        removed_count = 0

        for key in self.keys():
            if self.remove_child(key):
                removed_count += 1

        return removed_count

    # ------------------------------------------------------------------------
    # ACCESS LAYER - Child Retrieval
    # ------------------------------------------------------------------------

    def get_child(
        self,
        key: PathComponent,
        /,
    ) -> ChildInfo:
        """
        Get child information.

        This method retrieves child value and type.

        Args:
            key: Child key to retrieve.

        Returns:
            ChildInfo: Information about the child (exists, type, value).

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container malformed.

        Example:
            ```python
            child_info = container.get_child("key")
            print(f"Child {child_info.key}: {child_info.child_type}, Value: {child_info.value}")
        """
        self.validate_compatible

        return self.get_child_info(key)

    def get_primitive_child(
        self,
        key: PathComponent,
        /,
    ) -> Value | Empty:
        """Get primitive child value.

        Args:
            key: Child key to retrieve.

        Returns:
            Value | Empty: Primitive value if exists, EMPTY if not found.

        Raises:
            PathNotFoundError: If container doesn't exist.
            PathTypeError: If container incompatible.
            ContainerProtocolError: If container malformed.

        Example:
            ```python
            value = container.get_primitive_child("key")
            if value is not EMPTY:
                print(f"Primitive value: {value}")
            else:
                print("Primitive child does not exist")
            ```
        """
        self.validate_compatible

        child_info = self.get_child_info(key)
        if child_info.child_type == ChildType.PRIMITIVE:
            return child_info.value
        return EMPTY

    def keys(
        self, *, primitives_only: bool = False, skip_primitives: bool = False
    ) -> Generator[PathComponent, None, None]:
        """Get child keys with container health validation.

        Args:
            primitives_only: If True, only return primitive child keys.
            skip_primitives: If True, skip primitive keys and only return container keys.

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
        self.validate_compatible

        yield from self._get_keys_impl(
            primitives_only=primitives_only, skip_primitives=skip_primitives
        )

    def children(
        self, *, primitives_only: bool = False, skip_primitives: bool = False
    ) -> Generator[ChildInfo, None, None]:
        """Get child information with container health validation.

        Args:
            primitives_only: If True, only return primitive children.
            skip_primitives: If True, skip primitive children and only return container children.

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
        self.validate_compatible

        for key in self._get_keys_impl(
            primitives_only=primitives_only, skip_primitives=skip_primitives
        ):
            yield self.get_child_info(key)

    def _get_keys_impl(
        self, primitives_only: bool = False, skip_primitives: bool = False
    ) -> Generator[str, None, None]:
        """Implementation for key listing.

        Args:
            primitives_only: If True, only yield primitive keys.
            skip_primitives: If True, skip primitive keys and only yield container keys.

        Yields:
            str: Child keys.
        """
        try:
            for path_tuple in self.get_ensured_context().list_keys(self.path.to_tuple(), depth=1):
                key = path_tuple[-1]  # Get last component (key)

                # Determine child type to apply filters
                child_info = self.get_child_info(key)

                if primitives_only and child_info.child_type != ChildType.PRIMITIVE:
                    continue
                if skip_primitives and child_info.child_type == ChildType.PRIMITIVE:
                    continue

                yield key
        except StorageKeyError:
            pass  # Container might be empty

    def _delete_subtree(self, path: Path) -> bool:
        """
        Recursively delete a container and all its descendants.

        Args:
            path: Root path to delete

        Returns:
            bool: True if deleted, False if not found
        """
        # Collect all paths
        ctx = self.get_transaction_context()
        paths_to_delete: list[PathTuple] = []
        paths_to_delete.extend([p for p in ctx.list_keys(path.to_tuple(), depth=-1)])
        paths_to_delete.extend([p for p in ctx.list_keys(path.meta_path.to_tuple(), depth=-1)])
        paths_to_delete.extend(
            [
                path.to_tuple(),
                path.meta_path.to_tuple(),
            ]
        )

        # Remove duplicates
        set_paths_to_delete = set(paths_to_delete)

        # Keep track whether at least one path was deleted
        path_deleted = False

        for path_to_delete in set_paths_to_delete:
            try:
                ctx.delete(path_to_delete)
                path_deleted = True  # At least one path was successfully deleted
            except StorageKeyError:
                pass

        return path_deleted

    # =========================================================================
    # METADATA MANAGEMENT
    # =========================================================================

    def get_metadata(self, key: PathComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """
        Get metadata value (e.g., __length__ for ListView).

        Metadata is stored in the metadata path namespace.

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
        metadata_path = self.path.meta_path.join(key)
        try:
            return self.get_ensured_context().get(metadata_path.to_tuple())
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
        self.validate_mutable

        metadata_path = self.path.meta_path.join(key)
        self.get_transaction_context().set(metadata_path.to_tuple(), value)

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
        metadata_path = self.path.meta_path.join(key)
        return self.get_ensured_context().exists(metadata_path.to_tuple())

    def delete_metadata(self, key: PathComponent) -> bool:
        """
        Delete metadata key.

        Args:
            key: Metadata key to delete

        Returns:
            bool: True if metadata was deleted, False if it didn't exist

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
        self.validate_mutable

        metadata_path = self.path.meta_path.join(key)
        try:
            self.get_transaction_context().delete(metadata_path.to_tuple())
            return True
        except StorageKeyError:
            return False  # Metadata didn't exist
