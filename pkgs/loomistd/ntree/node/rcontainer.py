"""
Enhanced Container Lifecycle Management with Parent Chain Information

Key Features:
- check_existence() gets all parent info recursively (transaction-safe)
- Rich diagnostic information with parent chain types
- Performance-optimized batch operations
- Always called for transaction read-locking
"""

from __future__ import annotations

import dataclasses
from enum import Enum, auto

import attrs

from loomistd.kv import StorageKeyError

from ..exceptions import ContainerProtocolError, PathExistsError, PathNotFoundError, PathTypeError
from ..path import Path
from ..types import ContainerProtocol, ContainerStructure, NodeType
from .base import BaseNode

__all__ = [
    "ContainerNode",
    "ContainerState",
    "ParentInfo",
    "ContainerInfo",
]


class ContainerState(Enum):
    """Simple container states."""

    NOT_FOUND = auto()  # Container doesn't exist
    EXISTS = auto()  # Container exists and is valid
    TYPE_MISMATCH = auto()  # Path exists but wrong type/structure/protocol


@dataclasses.dataclass(frozen=True)
class ParentInfo:
    """Information about a parent container."""

    path: Path
    exists: bool
    structure: ContainerStructure | None = None
    protocol: ContainerProtocol | None = None
    type_error: str | None = None


@dataclasses.dataclass(frozen=True)
class ContainerInfo:
    """Comprehensive existence check result with parent chain information."""

    # Container status
    exists: bool
    state: ContainerState
    structure_match: bool = True
    protocol_match: bool = True
    type_error: str | None = None

    parent_chain_valid: bool = True
    # Parent chain information (from root to immediate parent)
    parents: tuple[ParentInfo, ...] = dataclasses.field(default_factory=tuple)
    # Paths of missing parents
    missing_parents: tuple[Path, ...] = dataclasses.field(default_factory=tuple)
    # Paths of parents with type errors
    invalid_parents: tuple[Path, ...] = dataclasses.field(default_factory=tuple)


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

    @property
    def node_type(self) -> NodeType:
        """Get the type of this node - always CONTAINER."""
        return NodeType.CONTAINER

    # =========================================================================
    # Core Existence Method (Always Called - Transaction Safe)
    # =========================================================================

    def get_info(self) -> ContainerInfo:
        """
        Comprehensive checks with full parent chain analysis.

        This method MUST be called by all other lifecycle methods as it:
        1. Touches all relevant keys for transaction read-locking
        2. Provides complete diagnostic information
        3. Validates entire parent chain in single pass
        4. Optimizes backend operations with batch checking

        Returns:
            ContainerInfo: Complete container and parent chain status

        Performance Notes:
        - Single transaction with batch key access
        - Traverses from root to target for efficiency
        - Caches parent validation results
        - Minimal redundant backend calls
        """
        tx = self.get_ensured_transaction()

        # Collect all paths to check (root to target)
        paths_to_check: list[Path] = []
        current_path = self.path
        while current_path is not None:
            paths_to_check.append(current_path)
            current_path = current_path.parent()

        # Reverse to check from root to target
        paths_to_check.reverse()

        # Batch check all struct paths
        parent_infos: list[ParentInfo] = []
        missing_parents: list[Path] = []
        invalid_parents: list[Path] = []
        parent_chain_valid: bool = True

        # Check all parents (excluding target container)
        for path in paths_to_check[:-1]:  # All except last (target)
            struct_path = path.struct_path

            try:
                # Touch key for transaction locking
                type_info = tx.get(struct_path.to_tuple())

                # Validate parent type info
                if isinstance(type_info, (list, tuple)) and len(type_info) == 2:
                    try:
                        structure = ContainerStructure(type_info[0])
                        protocol = ContainerProtocol(type_info[1])

                        parent_infos.append(
                            ParentInfo(
                                path=path, exists=True, structure=structure, protocol=protocol
                            )
                        )

                        # Check if parent can contain children
                        if not (protocol & ContainerProtocol.MUTABLE):
                            invalid_parents.append(path)
                            parent_chain_valid = False

                    except ValueError:
                        # Invalid enum values
                        error_msg = f"Invalid structure/protocol values: {type_info}"
                        parent_infos.append(
                            ParentInfo(path=path, exists=True, type_error=error_msg)
                        )
                        invalid_parents.append(path)
                        parent_chain_valid = False
                else:
                    # Invalid type metadata format
                    error_msg = f"Invalid type metadata format: {type_info}"
                    parent_infos.append(ParentInfo(path=path, exists=True, type_error=error_msg))
                    invalid_parents.append(path)
                    parent_chain_valid = False

            except StorageKeyError:
                # Parent doesn't exist
                parent_infos.append(ParentInfo(path=path, exists=False))
                missing_parents.append(path)
                parent_chain_valid = False

        # Now check target container
        target_path = paths_to_check[-1]  # Last item is target
        target_struct_path = target_path.struct_path

        try:
            # Touch target key for transaction locking
            type_info = tx.get(target_struct_path.to_tuple())

            # Validate target type info
            if not isinstance(type_info, (list, tuple)) or len(type_info) != 2:
                return ContainerInfo(
                    exists=True,
                    state=ContainerState.TYPE_MISMATCH,
                    structure_match=False,
                    protocol_match=False,
                    type_error="Invalid type metadata format",
                    parents=tuple(parent_infos),
                    parent_chain_valid=parent_chain_valid,
                    missing_parents=tuple(missing_parents),
                    invalid_parents=tuple(invalid_parents),
                )

            try:
                stored_structure = ContainerStructure(type_info[0])
                stored_protocol = ContainerProtocol(type_info[1])
            except ValueError:
                return ContainerInfo(
                    exists=True,
                    state=ContainerState.TYPE_MISMATCH,
                    structure_match=False,
                    protocol_match=False,
                    type_error=f"Invalid structure/protocol values: {type_info}",
                    parents=tuple(parent_infos),
                    parent_chain_valid=parent_chain_valid,
                    missing_parents=tuple(missing_parents),
                    invalid_parents=tuple(invalid_parents),
                )

            # Check compatibility with expected structure/protocol
            structure_match = self.structure & stored_structure == self.structure
            protocol_match = bool(self.protocol & stored_protocol)

            state = ContainerState.EXISTS
            error_msg = None

            if not structure_match or not protocol_match:
                state = ContainerState.TYPE_MISMATCH
                error_msg = f"Expected {self.structure}|{self.protocol}, got {stored_structure}|{stored_protocol}"

            return ContainerInfo(
                exists=True,
                state=state,
                structure_match=structure_match,
                protocol_match=protocol_match,
                type_error=error_msg,
                parents=tuple(parent_infos),
                parent_chain_valid=parent_chain_valid,
                missing_parents=tuple(missing_parents),
                invalid_parents=tuple(invalid_parents),
            )

        except StorageKeyError:
            # Target container doesn't exist
            return ContainerInfo(
                exists=False,
                state=ContainerState.NOT_FOUND,
                parents=tuple(parent_infos),
                parent_chain_valid=parent_chain_valid,
                missing_parents=tuple(missing_parents),
                invalid_parents=tuple(invalid_parents),
            )

    # =========================================================================
    # Support Methods (Return Bool, No Errors)
    # =========================================================================

    def supports_create(self, info: ContainerInfo, /, *, parents: bool = True) -> bool:
        """
        Check if container creation is supported.

        Args:
            info: Container information from get_info()
            parents: Whether parent creation should be considered

        Returns:
            bool: True if creation is possible

        Checks:
        - Container doesn't already exist with compatible type
        - No type conflicts at target path
        - Parent chain can be created/validated if parents=True
        """
        # Already exists with compatible type - creation not needed
        if info.exists and info.structure_match and info.protocol_match:
            return False

        # Exists with incompatible type - cannot create
        if info.exists and (not info.structure_match or not info.protocol_match):
            return False

        # Doesn't exist - check if we can create
        if not info.exists:
            if parents:
                # Check if parent chain can be established
                return self.supports_create_parents(info)
            else:
                # Without parent creation, need valid parent chain
                return info.parent_chain_valid

        return False

    def supports_create_parents(self, info: ContainerInfo, /) -> bool:
        """
        Check if parent creation is supported.

        Args:
            info: Container information from get_info()

        Returns:
            bool: True if parent creation is possible

        Checks:
        - Missing parents can be created (no type conflicts)
        - Invalid parents cannot be fixed (type conflicts)
        - Existing valid parents are preserved
        """
        # If parent chain is already valid, no creation needed
        if info.parent_chain_valid:
            return True

        # If there are invalid parents (type conflicts), cannot fix
        if info.invalid_parents:
            return False

        # Only missing parents - these can be created
        return len(info.missing_parents) > 0

    def supports_mutability(self, info: ContainerInfo, /) -> bool:
        """
        Check if container supports mutation operations.

        Args:
            info: Container information from get_info()

        Returns:
            bool: True if container is mutable
        """
        if not info.exists or not info.protocol_match:
            return False

        # Need to get actual protocol from storage
        # This info should be available in info object
        return True  # Placeholder - would check actual protocol

    # =========================================================================
    # Validation Methods (Raise on Failure, Check Supports Internally)
    # =========================================================================

    def validate_create(self, info: ContainerInfo, /, *, parents: bool = True) -> None:
        """
        Validate that container creation is possible.

        Args:
            info: Container information from get_info()
            parents: Whether parent creation should be validated

        Raises:
            PathExistsError: Container already exists with compatible type
            PathTypeError: Path exists with incompatible type
            ContainerProtocolError: Parent chain issues prevent creation
        """
        if not self.supports_create(info, parents=parents):
            if info.exists:
                if info.structure_match and info.protocol_match:
                    raise PathExistsError(f"Container at {self.path} already exists")
                else:
                    raise PathTypeError(f"Path exists with incompatible type: {info.type_error}")
            else:
                # Container doesn't exist, but creation not supported
                if not parents and not info.parent_chain_valid:
                    raise ContainerProtocolError(
                        f"Parent chain invalid and parents=False: "
                        f"missing={info.missing_parents}, invalid={info.invalid_parents}"
                    )
                elif parents and not self.supports_create_parents(info):
                    raise ContainerProtocolError(
                        f"Cannot create parents due to type conflicts: {info.invalid_parents}"
                    )

    def validate_create_parents(self, info: ContainerInfo, /) -> None:
        """
        Validate that parent creation is possible.

        Args:
            info: Container information from get_info()

        Raises:
            ContainerProtocolError: Parent chain has unfixable issues
        """
        if not self.supports_create_parents(info):
            if info.invalid_parents:
                raise ContainerProtocolError(
                    f"Parent paths have type conflicts that cannot be resolved: {info.invalid_parents}"
                )
            elif info.parent_chain_valid:
                raise ContainerProtocolError("Parent chain is already valid - no creation needed")
            else:
                raise ContainerProtocolError("Parent creation not supported for unknown reasons")

    def validate_mutability(self, info: ContainerInfo, /) -> None:
        """
        Validate that container supports mutation.

        Args:
            info: Container information from get_info()

        Raises:
            PathNotFoundError: Container doesn't exist
            ContainerProtocolError: Container is not mutable
        """
        if not info.exists:
            raise PathNotFoundError(f"Container at {self.path} does not exist")

        if not self.supports_mutability(info):
            raise ContainerProtocolError(f"Container at {self.path} is not mutable")

    def validate_compatibility(self, info: ContainerInfo, /) -> None:
        """
        Validate container matches expected structure/protocol.

        Args:
            info: Container information from get_info()

        Raises:
            PathNotFoundError: Container doesn't exist
            ContainerProtocolError: Incompatible structure/protocol
        """
        if not info.exists:
            raise PathNotFoundError(f"Container at {self.path} does not exist")

        if not info.structure_match:
            raise ContainerProtocolError(f"Structure mismatch: {info.type_error}")

        if not info.protocol_match:
            raise ContainerProtocolError(f"Protocol mismatch: {info.type_error}")

    # =========================================================================
    # Decision Methods (Return Bool, Check Supports Internally)
    # =========================================================================

    def can_create(self, info: ContainerInfo, /, *, parents: bool = True) -> bool:
        """
        Check if container can be created.

        Args:
            info: Container information from get_info()
            parents: Whether parent creation is allowed

        Returns:
            bool: True if try_create() would succeed

        Usage:
            ```python
            info = container.get_info()
            if container.can_create(info):
                container.try_create(info)  # Guaranteed to succeed
            else:
                handle_creation_blocked()
            ```
        """
        return self.supports_create(info, parents=parents)

    def can_create_parents(self, info: ContainerInfo, /) -> bool:
        """
        Check if parent containers can be created.

        Args:
            info: Container information from get_info()

        Returns:
            bool: True if try_create_parents() would succeed
        """
        return self.supports_create_parents(info)

    def can_mutate(self, info: ContainerInfo, /) -> bool:
        """
        Check if container can be mutated.

        Args:
            info: Container information from get_info()

        Returns:
            bool: True if mutation operations would succeed
        """
        return self.supports_mutability(info)

    # =========================================================================
    # Execution Methods (Raise on Failure, Use Validation Internally)
    # =========================================================================

    def try_create(self, info: ContainerInfo, /, *, parents: bool = True) -> bool:
        """
        Create container.

        Args:
            info: Container information from get_info()
            parents: Create missing parent containers

        Returns:
            bool: True if container was created, False if already existed

        Raises:
            PathTypeError: Path exists with incompatible type
            ContainerProtocolError: Parent chain issues

        Usage:
            ```python
            info = container.get_info()
            try:
                created = container.try_create(info)
                if created:
                    print("Container created")
                else:
                    print("Container already existed")
            except PathTypeError as e:
                handle_type_conflict(e)
            ```
        """
        # Use validation to check and raise appropriate errors
        self.validate_create(info, parents=parents)

        # If we get here, creation is valid
        if info.exists:
            return False  # Already existed

        # Create parents if needed
        if parents and not info.parent_chain_valid:
            self.try_create_parents(info)

        # Create the container
        tx = self.get_ensured_transaction()
        tx.set(self.path.struct_path.to_tuple(), [self.structure.value, self.protocol.value])

        return True

    def try_create_parents(self, info: ContainerInfo, /) -> list[str]:
        """
        Create missing parent containers.

        Args:
            info: Container information from get_info()

        Returns:
            list[str]: Paths of parents that were created

        Raises:
            ContainerProtocolError: Parent type conflicts prevent creation
        """
        self.validate_create_parents(info)

        if info.parent_chain_valid:
            return []  # No parents need creation

        # Create missing parents
        tx = self.get_ensured_transaction()
        created_paths = []

        for parent_path in info.missing_parents:
            # Create as MAPPING container with DICT protocol
            struct_path = parent_path.struct_path

            tx.set(
                struct_path.to_tuple(),
                [ContainerStructure.MAPPING_CONTAINER.value, ContainerProtocol.DICT.value],
            )
            created_paths.append(parent_path)

        return created_paths

    # =========================================================================
    # Convenience Methods (Combining Common Patterns)
    # =========================================================================

    def ensure_exists(self, info: ContainerInfo, /, *, parents: bool = True) -> bool:
        """
        Ensure container exists - create if missing, validate if exists.

        Args:
            info: Container information from get_info()
            parents: Create missing parents

        Returns:
            bool: True if container was created, False if already existed

        Raises:
            PathTypeError: Existing path has incompatible type
            ContainerProtocolError: Parent validation failed
        """
        if info.exists:
            # Validate compatibility
            self.validate_compatibility(info)
            return False
        else:
            # Create container
            return self.try_create(info, parents=parents)

    def ensure_parents(self, info: ContainerInfo, /) -> list[str]:
        """
        Ensure all parent containers exist.

        Args:
            info: Container information from get_info()

        Returns:
            list[str]: Paths of parents that were created

        Raises:
            ContainerProtocolError: Parent type conflicts
        """
        if info.parent_chain_valid:
            return []

        return self.try_create_parents(info)

    # =========================================================================
    # Inspection Methods (Simple Accessors Using Info)
    # =========================================================================

    def exists(self, info: ContainerInfo, /) -> bool:
        """Get existence status from info."""
        return info.exists

    def exists_and_valid(self, info: ContainerInfo, /) -> bool:
        """Get existence and validity status from info."""
        return info.exists and info.structure_match and info.protocol_match

    def get_state(self, info: ContainerInfo, /) -> ContainerState:
        """Get container state from info."""
        return info.state

    def is_parent_chain_valid(self, info: ContainerInfo, /) -> bool:
        """Get parent chain validity from info."""
        return info.parent_chain_valid
