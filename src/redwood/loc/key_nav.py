"""Key traversal and navigation operations.

This module provides pure key manipulation functions with no storage access.
All functions are stateless and can be safely cached or memoized.

Performance notes:
- All operations are pure functions on tuples
- Heavy use of tuple slicing which is highly optimized in CPython
- Short-circuit evaluation for boolean checks
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .key_def import Key, KeySegment

__all__ = [
    "DATA_ROOT",
    "METADATA_ROOT",
    "create_key",
    "get_ancestors",
    "get_common_ancestor",
    "get_depth",
    "get_key_chain",
    "get_parent",
    "is_ancestor",
    "is_descendant",
    "is_sibling",
    "join_key",
    "join_segment",
    "to_meta",
]

# Root marker for the root data segment (stores actual data)
DATA_ROOT: str = "/"
# Root marker for the metadata segment (stores metadata)
METADATA_ROOT: str = "/m"


def create_key(*segments: KeySegment) -> Key:
    """Creata a key from given segments.

    Args:
        *segments: Key segments

    Returns:
        Single key (includes tree root </>)

    Example:
        >>> get_parent(("users", "alice"))
        ("/", "users", "alice")
    """
    return (DATA_ROOT, *segments)


def to_meta(key: Key) -> Key:
    """Convert a key to its metadata equivalent.

    Args:
        key: Key tuple

    Returns:
        tuple: New key with metadata root marker

    Example:
        >>> key = create_key("users", "alice")
        >>> key
        ("/", "users", "alice")
        >>> to_meta(key)
        ("/m", "users", "alice")
        ```
    """
    return (METADATA_ROOT, *key[1:])


def get_parent(key: Key) -> Key | None:
    """Get parent key.

    Args:
        key: Key to get parent of

    Returns:
        Parent key, or None for empty key

    Example:
        >>> get_parent(("users", "alice"))
        ("users",)
        >>> get_parent(())
        None
    """
    if len(key) <= 1:
        return None

    return key[:-1]


def get_ancestors(key: Key) -> list[Key]:
    """Get all ancestors from root to immediate parent.

    Returns ancestors in order from root (empty tuple) to immediate parent.
    Does not include the key itself.

    Args:
        key: Key to get ancestors of

    Returns:
        List of ancestor keys, empty list for root

    Example:
        >>> get_ancestors(("users", "alice", "profile"))
        [(), ("users",), ("users", "alice")]
    """
    if len(key) <= 1:
        return []

    ancestors = []
    current = key[:-1]  # Start with immediate parent

    while current is not None:
        ancestors.append(current)
        current = get_parent(current)

    return list(reversed(ancestors))


def get_key_chain(key: Key) -> list[Key]:
    """Get complete key chain from root to target.

    Returns all keys from root to target, including the target itself.

    Args:
        key: Target key

    Returns:
        List of keys from root to target (inclusive)

    Example:
        >>> get_key_chain(("users", "alice"))
        [(), ("users",), ("users", "alice")]
    """
    chain = get_ancestors(key)
    chain.append(key)
    return chain


def is_ancestor(parent: Key, child: Key) -> bool:
    """Check if parent is ancestor of child.

    A key is considered an ancestor if it's a prefix of the child key
    and strictly shorter.

    Args:
        parent: Potential ancestor key
        child: Potential descendant key

    Returns:
        True if parent is ancestor of child

    Example:
        >>> is_ancestor(("users",), ("users", "alice"))
        True
        >>> is_ancestor(("users", "alice"), ("users",))
        False
    """
    # Hot key optimization: check length first (cheap), then slice (more expensive)
    return len(parent) < len(child) and child[: len(parent)] == parent


def is_descendant(child: Key, parent: Key) -> bool:
    """Check if child is descendant of parent.

    Convenience wrapper around is_ancestor with reversed arguments.

    Args:
        child: Potential descendant key
        parent: Potential ancestor key

    Returns:
        True if child is descendant of parent

    Example:
        >>> is_descendant(("users", "alice"), ("users",))
        True
    """
    return is_ancestor(parent, child)


def is_sibling(key1: Key, key2: Key) -> bool:
    """Check if two keys are siblings.

    Siblings share the same parent key and are at the same depth.

    Args:
        key1: First key
        key2: Second key

    Returns:
        True if keys are siblings

    Example:
        >>> is_sibling(("users", "alice"), ("users", "bob"))
        True
        >>> is_sibling(("users", "alice"), ("posts", "1"))
        False
    """
    # Must be same depth (non-zero) and same parent
    if not key1 or not key2:
        return False
    if len(key1) != len(key2):
        return False
    return key1[:-1] == key2[:-1]


def get_depth(key: Key) -> int:
    """Get depth of key.

    Depth is the number of segments in the key. Root (empty tuple) has depth 0.

    Args:
        key: Key to measure

    Returns:
        Depth (length) of key

    Example:
        >>> get_depth(())
        0
        >>> get_depth(("users", "alice"))
        2
    """
    return len(key)


def join_key(*segments: KeySegment | Key) -> Key:
    """Join key segments into a single key.

    Handles both individual segments and tuple keys, flattening them
    into a single tuple key.

    Args:
        *segments: Key segments or tuple keys to join

    Returns:
        Combined key as tuple

    Example:
        >>> join_key("users", "alice")
        ("users", "alice")
        >>> join_key(("users",), "alice", "profile")
        ("users", "alice", "profile")
    """
    result = []
    for segment in segments:
        if isinstance(segment, tuple):
            result.extend(segment)
        else:
            result.append(segment)
    return tuple(result)


def join_segment(key: Key, *segments: KeySegment) -> Key:
    """Join key segments into a single key.

    Adds new segments to the original key.

    Args:
        key: Original key
        *segments: Components to join

    Returns:
        Combined key as tuple
    """
    return key + segments


def get_common_ancestor(key1: Key, key2: Key) -> Key:
    """Find lowest common ancestor of two keys.

    Returns the deepest key that is an ancestor of both input keys.

    Args:
        key1: First key
        key2: Second key

    Returns:
        Common ancestor key (may be empty tuple for root)

    Example:
        >>> get_common_ancestor(("users", "alice", "posts"), ("users", "bob"))
        ("users",)
        >>> get_common_ancestor(("users", "alice"), ("posts", "1"))
        ()
    """
    # Find common prefix
    min_len = min(len(key1), len(key2))
    common_len = 0

    for i in range(min_len):
        if key1[i] == key2[i]:
            common_len = i + 1
        else:
            break

    return key1[:common_len]
