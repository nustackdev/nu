"""Metadata operations for containers.

This module provides metadata management operations. Metadata is stored in
the /m parallel tree and must be flat primitive values (no containers).

All operations are stateless functions that operate on paths and contexts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.loc import key
from everyshape.storage import StorageKeyError

from .types import (
    require_read_context,
    require_write_context,
)


if TYPE_CHECKING:
    from collections.abc import Generator

    from everyshape.storage import StorageContextType
    from everyshape.types import Empty, Value

__all__ = [
    "delete_metadata",
    "get_metadata",
    "has_metadata",
    "list_metadata_keys",
    "set_metadata",
]


def set_metadata(
    path: key.Key, key_segment: key.KeySegment, value: Value, ctx: StorageContextType
) -> None:
    """Set metadata for container at path.

    Args:
        path: Container path
        key_segment: Metadata key
        value: Primitive value to store
        ctx: Storage context

    Raises:
        StorageInterfaceError: If context doesn't support writes
    """
    meta_path = key.join_segment(key.to_meta(path), key_segment)
    require_write_context(ctx).put(meta_path, value)


def get_metadata(
    path: key.Key,
    key_segment: key.KeySegment,
    ctx: StorageContextType,
    default: Value | Empty = None,
) -> Value | Empty:
    """Get metadata value for container at path.

    Args:
        path: Container path
        key_segment: Metadata key
        ctx: Storage context
        default: Default value if not found

    Returns:
        Metadata value or default if doesn't exist

    Raises:
        StorageInterfaceError: If context doesn't support reads
    """
    meta_path = key.join_segment(key.to_meta(path), key_segment)
    try:
        return require_read_context(ctx).get(meta_path)
    except StorageKeyError:
        return default


def has_metadata(path: key.Key, key_segment: key.KeySegment, ctx: StorageContextType) -> bool:
    """Check if metadata key exists for container at path.

    Args:
        path: Container path
        key_segment: Metadata key
        ctx: Storage context

    Returns:
        True if metadata exists

    Raises:
        StorageInterfaceError: If context doesn't support reads
    """
    meta_path = key.join_segment(key.to_meta(path), key_segment)
    return require_read_context(ctx).has(meta_path)


def delete_metadata(path: key.Key, key_segment: key.KeySegment, ctx: StorageContextType) -> bool:
    """Delete metadata key for container at path.

    Args:
        path: Container path
        key_segment: Metadata key
        ctx: Storage context

    Returns:
        True if deleted, False if didn't exist

    Raises:
        StorageInterfaceError: If context doesn't support writes
    """
    meta_path = key.join_segment(key.to_meta(path), key_segment)
    return require_write_context(ctx).delete(meta_path)


def list_metadata_keys(
    path: key.Key, ctx: StorageContextType
) -> Generator[key.KeySegment, None, None]:
    """List all metadata keys for container at path.

    Args:
        path: Container path
        ctx: Storage context

    Yields:
        Metadata keys

    Raises:
        StorageInterfaceError: If context doesn't support reads
    """
    from everyshape.storage import StorageScanOptions

    meta_path = key.to_meta(path)
    # Scan immediate children of metadata path only (length = meta_path + 1)
    options = StorageScanOptions(
        start=key.join_segment(meta_path, ""),
        end=key.join_segment(meta_path, "\uffff"),
        length=len(meta_path) + 1,
    )
    for meta_key in require_read_context(ctx).scan(options).keys():
        # Extract last segment (metadata key)
        yield meta_key[-1]
