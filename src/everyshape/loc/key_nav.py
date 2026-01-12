"""Key construction and flat operations.

This module provides pure key manipulation functions for the Storage layer.
Keys are raw tuple coordinates without hierarchical semantics.

For hierarchical operations (ancestors, descendants, etc.), use the site module.

Key vs Site semantics:
    - Key: flat storage coordinates, construction and join operations
    - Site: hierarchical place, ancestor/descendant relationships

Performance notes:
    - All operations are pure functions on tuples
    - Highly optimized tuple operations in CPython
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .constants import DATA_ROOT, METADATA_ROOT


if TYPE_CHECKING:
    from .key_def import Key, KeySegment

__all__ = [
    "create_key",
    "get_depth",
    "join_key",
    "join_segment",
    "to_meta",
]


def create_key(*segments: KeySegment) -> Key:
    """Create a key from given segments with data root.

    Args:
        *segments: Key segments

    Returns:
        Key tuple with DATA_ROOT prefix

    Example:
        >>> create_key("users", "alice")
        ("/", "users", "alice")
        >>> create_key()
        ("/",)
    """
    return (DATA_ROOT, *segments)


def to_meta(key: Key) -> Key:
    """Convert a key to its metadata equivalent.

    Replaces the root marker with METADATA_ROOT.

    Args:
        key: Key tuple (must start with DATA_ROOT)

    Returns:
        Key with metadata root marker

    Example:
        >>> key = create_key("users", "alice")
        >>> key
        ("/", "users", "alice")
        >>> to_meta(key)
        ("/m", "users", "alice")
    """
    return (METADATA_ROOT, *key[1:])


def get_depth(key: Key) -> int:
    """Get depth (length) of key.

    Args:
        key: Key to measure

    Returns:
        Number of segments in the key

    Example:
        >>> get_depth(())
        0
        >>> get_depth(("users",))
        1
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
        >>> join_key(("a", "b"), ("c", "d"))
        ("a", "b", "c", "d")
    """
    result = []
    for segment in segments:
        if isinstance(segment, tuple):
            result.extend(segment)
        else:
            result.append(segment)
    return tuple(result)


def join_segment(key: Key, *segments: KeySegment) -> Key:
    """Append segments to a key.

    Args:
        key: Base key
        *segments: Segments to append

    Returns:
        Key with segments appended

    Example:
        >>> join_segment(("users",), "alice")
        ("users", "alice")
        >>> join_segment(("/",), "users", "alice")
        ("/", "users", "alice")
    """
    return key + segments
