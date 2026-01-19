"""Container layer - hierarchical semantics over flat tuple-key-value storage.

The container layer (Layer 2) provides hierarchical organization over the flat
key-value storage (Layer 1). It interprets tuple keys as parent-child sites
and distinguishes containers (nodes with children) from primitives (leaf values).

Core Responsibilities:
    - Interpret tuple keys as hierarchical sites
    - Distinguish containers from primitives using markers
    - Enforce parent-must-exist-before-child rule
    - Provide container type markers for View reconstruction

The container layer does NOT:
    - Implement data structures (that's Views Layer 3)
    - Handle application logic (that's Semantics Layer 4)
    - Know about dict/list/queue semantics

Architecture:
    The module is organized into focused, composable components:
    - types: Type definitions and data structures
    - exceptions: Container-specific error hierarchy
    - marker: Container type marker system
    - node_ops: Node identification and information
    - validation_ops: Rule enforcement
    - container_ops: Container operations and children management
    - meta_ops: Metadata operations
    - container: Container convenience class

All mutations are silent (return None) and idempotent.
"""

from __future__ import annotations

# ============================================================================
# Main Interface: Container
# ============================================================================
from .container import Container

# ============================================================================
# Container Operations
# ============================================================================
from .container_ops import (
    clear_children,
    count_children,
    create_child_container,
    create_container,
    create_parents,
    delete_child,
    delete_container,
    delete_descendants,
    exists_child,
    get_child_primitive,
    get_child_type,
    iter_child_keys,
    iter_child_values,
    iter_children,
    iter_descendants,
    put_child_primitive,
    walk_descendants,
)

# ============================================================================
# Context
# ============================================================================
from .context import (
    require_read_context,
    require_readwrite_context,
    require_snapshot,
    require_transaction,
    require_write_batch,
    require_write_context,
)

# ============================================================================
# Exceptions
# ============================================================================
from .exceptions import (
    ContainerCollisionError,
    ContainerError,
    ContainerExistsError,
    ContainerInvalidDepthError,
    ContainerInvalidSiteError,
    ContainerNotFoundError,
    ContainerParentMalformedError,
    ContainerParentNotFoundError,
    ContainerTypeError,
)

# ============================================================================
# Marker System
# ============================================================================
from .marker import (
    MARKER_SENTINEL,
    create_marker,
    extract_marker,
    is_marker,
    validate_marker_compatibility,
)

# ============================================================================
# Metadata Operations
# ============================================================================
from .meta_ops import (
    delete_metadata,
    exists_metadata,
    get_metadata,
    iter_metadata_keys,
    put_metadata,
)

# ============================================================================
# Node Operations
# ============================================================================
from .node_ops import (
    gather_parent_info,
    get_node_info,
    get_node_type,
    node_exists,
)

# ============================================================================
# Types and Data Structures
# ============================================================================
from .types import (
    DEFAULT_PARENT_PROTOCOL,
    DEFAULT_PARENT_STRUCTURE,
    ContainerProtocol,
    ContainerStructure,
    NodeInfo,
    NodeType,
    ParentChainInfo,
    ParentInfo,
)

# ============================================================================
# Validation Operations
# ============================================================================
from .validation_ops import (
    validate_compatible,
    validate_exists,
    validate_is_container,
    validate_is_primitive,
    validate_not_exists,
    validate_parents_chain,
    validate_parents_exist,
    validate_parents_healthy,
)


# ============================================================================
# Public API
# ============================================================================

__all__ = [  # noqa: RUF022
    # Types
    "NodeType",
    "ContainerStructure",
    "ContainerProtocol",
    "NodeInfo",
    "ParentInfo",
    "ParentChainInfo",
    "DEFAULT_PARENT_STRUCTURE",
    "DEFAULT_PARENT_PROTOCOL",
    # Exceptions
    "ContainerError",
    "ContainerNotFoundError",
    "ContainerExistsError",
    "ContainerInvalidSiteError",
    "ContainerTypeError",
    "ContainerCollisionError",
    "ContainerParentNotFoundError",
    "ContainerParentMalformedError",
    "ContainerInvalidDepthError",
    # Marker system
    "MARKER_SENTINEL",
    "create_marker",
    "extract_marker",
    "is_marker",
    "validate_marker_compatibility",
    # Node operations
    "get_node_info",
    "get_node_type",
    "node_exists",
    "gather_parent_info",
    # Validation
    "validate_exists",
    "validate_not_exists",
    "validate_is_container",
    "validate_is_primitive",
    "validate_parents_exist",
    "validate_parents_healthy",
    "validate_parents_chain",
    "validate_compatible",
    # Container operations
    "create_container",
    "delete_container",
    "delete_descendants",
    "exists_child",
    "get_child_type",
    "get_child_primitive",
    "iter_child_keys",
    "iter_child_values",
    "iter_children",
    "count_children",
    "create_child_container",
    "put_child_primitive",
    "delete_child",
    "clear_children",
    "iter_descendants",
    "walk_descendants",
    "create_parents",
    # Metadata operations
    "put_metadata",
    "get_metadata",
    "exists_metadata",
    "delete_metadata",
    "iter_metadata_keys",
    # Main interface
    "Container",
    # Context
    "require_read_context",
    "require_readwrite_context",
    "require_snapshot",
    "require_transaction",
    "require_write_batch",
    "require_write_context",
]
