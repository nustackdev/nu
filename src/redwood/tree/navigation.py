"""Path traversal and navigation operations.

This module provides pure path manipulation functions with no storage access.
All functions are stateless and can be safely cached or memoized.

Performance notes:
- All operations are pure functions on tuples
- Heavy use of tuple slicing which is highly optimized in CPython
- Short-circuit evaluation for boolean checks
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.abc import KeyComponent, TupleKey

__all__ = [
    "create_path",
    "get_ancestors",
    "get_common_ancestor",
    "get_depth",
    "get_parent",
    "get_path_chain",
    "is_ancestor",
    "is_descendant",
    "is_sibling",
    "join_component",
    "join_path",
    "to_meta",
]

# Root marker for the root data component (stores actual data)
DATA_ROOT: str = "/"
# Root marker for the metadata component (stores metadata)
METADATA_ROOT: str = "/m"


def create_path(*components: KeyComponent) -> TupleKey:
    """Creata a path from given components.

    Args:
        *components: Path components

    Returns:
        Single path (includes tree root </>)

    Example:
        >>> get_parent(("users", "alice"))
        ("/", "users", "alice")
    """
    return (DATA_ROOT, *components)


def to_meta(path: TupleKey) -> TupleKey:
    """Convert a path to its metadata equivalent.

    Args:
        path: Path tuple

    Returns:
        tuple: New path with metadata root marker

    Example:
        >>> path = create_path("users", "alice")
        >>> path
        ("/", "users", "alice")
        >>> to_meta(path)
        ("/m", "users", "alice")
        ```
    """
    return (METADATA_ROOT, *path[1:])


def get_parent(path: TupleKey) -> TupleKey | None:
    """Get parent path.

    Args:
        path: Path to get parent of

    Returns:
        Parent path, or None for empty path

    Example:
        >>> get_parent(("users", "alice"))
        ("users",)
        >>> get_parent(())
        None
    """
    if len(path) <= 1:
        return None

    return path[:-1]


def get_ancestors(path: TupleKey) -> list[TupleKey]:
    """Get all ancestors from root to immediate parent.

    Returns ancestors in order from root (empty tuple) to immediate parent.
    Does not include the path itself.

    Args:
        path: Path to get ancestors of

    Returns:
        List of ancestor paths, empty list for root

    Example:
        >>> get_ancestors(("users", "alice", "profile"))
        [(), ("users",), ("users", "alice")]
    """
    if len(path) <= 1:
        return []

    ancestors = []
    current = path[:-1]  # Start with immediate parent

    while current is not None:
        ancestors.append(current)
        current = get_parent(current)

    return list(reversed(ancestors))


def get_path_chain(path: TupleKey) -> list[TupleKey]:
    """Get complete path chain from root to target.

    Returns all paths from root to target, including the target itself.

    Args:
        path: Target path

    Returns:
        List of paths from root to target (inclusive)

    Example:
        >>> get_path_chain(("users", "alice"))
        [(), ("users",), ("users", "alice")]
    """
    chain = get_ancestors(path)
    chain.append(path)
    return chain


def is_ancestor(parent: TupleKey, child: TupleKey) -> bool:
    """Check if parent is ancestor of child.

    A path is considered an ancestor if it's a prefix of the child path
    and strictly shorter.

    Args:
        parent: Potential ancestor path
        child: Potential descendant path

    Returns:
        True if parent is ancestor of child

    Example:
        >>> is_ancestor(("users",), ("users", "alice"))
        True
        >>> is_ancestor(("users", "alice"), ("users",))
        False
    """
    # Hot path optimization: check length first (cheap), then slice (more expensive)
    return len(parent) < len(child) and child[: len(parent)] == parent


def is_descendant(child: TupleKey, parent: TupleKey) -> bool:
    """Check if child is descendant of parent.

    Convenience wrapper around is_ancestor with reversed arguments.

    Args:
        child: Potential descendant path
        parent: Potential ancestor path

    Returns:
        True if child is descendant of parent

    Example:
        >>> is_descendant(("users", "alice"), ("users",))
        True
    """
    return is_ancestor(parent, child)


def is_sibling(path1: TupleKey, path2: TupleKey) -> bool:
    """Check if two paths are siblings.

    Siblings share the same parent path and are at the same depth.

    Args:
        path1: First path
        path2: Second path

    Returns:
        True if paths are siblings

    Example:
        >>> is_sibling(("users", "alice"), ("users", "bob"))
        True
        >>> is_sibling(("users", "alice"), ("posts", "1"))
        False
    """
    # Must be same depth (non-zero) and same parent
    if not path1 or not path2:
        return False
    if len(path1) != len(path2):
        return False
    return path1[:-1] == path2[:-1]


def get_depth(path: TupleKey) -> int:
    """Get depth of path.

    Depth is the number of components in the path. Root (empty tuple) has depth 0.

    Args:
        path: Path to measure

    Returns:
        Depth (length) of path

    Example:
        >>> get_depth(())
        0
        >>> get_depth(("users", "alice"))
        2
    """
    return len(path)


def join_path(*components: KeyComponent | TupleKey) -> TupleKey:
    """Join path components into a single path.

    Handles both individual components and tuple paths, flattening them
    into a single tuple path.

    Args:
        *components: Path components or tuple paths to join

    Returns:
        Combined path as tuple

    Example:
        >>> join_path("users", "alice")
        ("users", "alice")
        >>> join_path(("users",), "alice", "profile")
        ("users", "alice", "profile")
    """
    result = []
    for component in components:
        if isinstance(component, tuple):
            result.extend(component)
        else:
            result.append(component)
    return tuple(result)


def join_component(path: TupleKey, *components: KeyComponent) -> TupleKey:
    """Join path components into a single path.

    Adds new components to the original path.

    Args:
        path: Original path
        *components: Components to join

    Returns:
        Combined path as tuple
    """
    return path + components


def get_common_ancestor(path1: TupleKey, path2: TupleKey) -> TupleKey:
    """Find lowest common ancestor of two paths.

    Returns the deepest path that is an ancestor of both input paths.

    Args:
        path1: First path
        path2: Second path

    Returns:
        Common ancestor path (may be empty tuple for root)

    Example:
        >>> get_common_ancestor(("users", "alice", "posts"), ("users", "bob"))
        ("users",)
        >>> get_common_ancestor(("users", "alice"), ("posts", "1"))
        ()
    """
    # Find common prefix
    min_len = min(len(path1), len(path2))
    common_len = 0

    for i in range(min_len):
        if path1[i] == path2[i]:
            common_len = i + 1
        else:
            break

    return path1[:common_len]
