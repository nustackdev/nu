"""Metadata operations for containers.

This module provides metadata management operations. Metadata is stored in
the /m parallel tree and must be flat primitive values (no containers).

All operations are stateless functions that operate on paths and contexts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyshape.loc import key
from everyshape.types import EMPTY

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
    value = require_read_context(ctx).get(meta_path)
    if value is EMPTY:
        return default
    return value


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
    return require_read_context(ctx).exists(meta_path)


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
    wctx = require_write_context(ctx)
    existed = wctx.exists(meta_path)
    wctx.delete(meta_path)
    return existed


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
    from everyshape.storage import LengthFilter, PrefixFilter, StorageScanOptions

    meta_path = key.to_meta(path)
    # Scan immediate children of metadata path only (length = meta_path + 1)
    prefix = PrefixFilter(prefix=meta_path)
    child_len = LengthFilter(length=len(meta_path) + 1)
    options = StorageScanOptions(
        start=(*meta_path, ""),  # Start after meta_path itself
        break_filter=prefix,
        filter=prefix & child_len,
    )
    for meta_key in require_read_context(ctx).scan(options).keys():
        # Extract last segment (metadata key)
        yield meta_key[-1]
