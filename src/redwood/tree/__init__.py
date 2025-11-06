"""Tree layer - hierarchical semantics over flat tuple-key-value storage.

The tree layer (Layer 2) provides hierarchical organization over the flat
key-value storage (Layer 1). It interprets tuple keys as parent-child paths
and distinguishes containers (nodes with children) from primitives (leaf values).

Core Responsibilities:
    - Interpret tuple keys as hierarchical paths
    - Distinguish containers from primitives using markers
    - Enforce parent-must-exist-before-child rule
    - Provide container type markers for View reconstruction

The tree layer does NOT:
    - Implement data structures (that's Views Layer 3)
    - Handle application logic (that's Semantics Layer 4)
    - Know about dict/list/queue semantics

Architecture:
    The module is organized into focused, composable components:
    - types: Type definitions and data structures
    - exceptions: Tree-specific error hierarchy
    - marker: Container type marker system
    - node: Node identification and information
    - navigation: Path traversal (pure functions)
    - validation: Rule enforcement
    - container: Container operations and children management
    - tree: Main convenience interface

Usage:
    Direct functional API (recommended for library code):
        >>> from redwood.tree import create_container, get_node_info
        >>> with storage.transaction() as tx:
        ...     create_container(
        ...         ("users",), ContainerStructure(1), ContainerProtocol.MUTABLE, tx
        ...     )
        ...     info = get_node_info(("users",), tx)

    Object-oriented API (convenient for application code):
        >>> from redwood.tree import Tree
        >>> with storage.transaction() as tx:
        ...     tree = Tree(ctx=tx)
        ...     tree.create_container(
        ...         ("users",), ContainerStructure(1), ContainerProtocol.MUTABLE
        ...     )
        ...     info = tree.get_node_info(("users",))
"""

from __future__ import annotations

# ============================================================================
# Container Operations
# ============================================================================
from .container import (
    clear_children,
    count_children,
    create_child_container,
    create_container,
    create_parents,
    delete_child,
    delete_container,
    delete_subtree,
    ensure_parents,
    get_child_type,
    has_child,
    list_child_keys,
    list_children,
    list_descendants,
    set_child_primitive,
    walk_tree,
)

# ============================================================================
# Exceptions
# ============================================================================
from .exceptions import (
    InvalidDepthError,
    ParentMalformedError,
    ParentNotFoundError,
    PathCollisionError,
    PathExistsError,
    PathNotFoundError,
    PathTypeError,
    TreeError,
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
# Navigation Operations (Pure Functions)
# ============================================================================
from .navigation import (
    get_ancestors,
    get_common_ancestor,
    get_depth,
    get_parent,
    get_path_chain,
    is_ancestor,
    is_descendant,
    is_sibling,
    join_path,
    split_path,
)

# ============================================================================
# Node Operations
# ============================================================================
from .node import (
    get_node_info,
    get_node_type,
    node_exists,
)

# ============================================================================
# Main Tree Interface
# ============================================================================
from .tree import Tree

# ============================================================================
# Types and Data Structures
# ============================================================================
from .types import (
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
from .validation import (
    gather_parent_info,
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
    # Exceptions
    "TreeError",
    "PathNotFoundError",
    "PathExistsError",
    "PathTypeError",
    "PathCollisionError",
    "ParentNotFoundError",
    "ParentMalformedError",
    "InvalidDepthError",
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
    # Navigation (pure functions)
    "get_parent",
    "get_ancestors",
    "get_path_chain",
    "is_ancestor",
    "is_descendant",
    "is_sibling",
    "get_depth",
    "join_path",
    "split_path",
    "get_common_ancestor",
    # Validation
    "gather_parent_info",
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
    "delete_subtree",
    "has_child",
    "get_child_type",
    "list_child_keys",
    "list_children",
    "count_children",
    "create_child_container",
    "set_child_primitive",
    "delete_child",
    "clear_children",
    "list_descendants",
    "walk_tree",
    "create_parents",
    "ensure_parents",
    # Main interface
    "Tree",
]
