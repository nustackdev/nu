"""Metadata operations for containers.

This module provides metadata management operations. Metadata is stored in
the /m parallel tree and must be flat primitive values (no containers).

All operations are stateless functions that operate on sites and contexts.
All mutations are silent (return None) and idempotent.
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

    from everyshape.loc import site as site_
    from everyshape.storage import StorageContextType
    from everyshape.types import Empty, Value

__all__ = [
    "delete_metadata",
    "exists_metadata",
    "get_metadata",
    "iter_metadata_keys",
    "put_metadata",
]


def put_metadata(
    site: site_.Site, key_segment: key.KeySegment, value: Value, ctx: StorageContextType
) -> None:
    """Put metadata for container at site.

    Idempotent: overwrites if already exists.

    Args:
        site: Container site
        key_segment: Metadata key
        value: Primitive value to store
        ctx: Storage context

    Raises:
        StorageInterfaceError: If context doesn't support writes
    """
    meta_site = key.join_segment(key.to_meta(site), key_segment)
    require_write_context(ctx).put(meta_site, value)


def get_metadata(
    site: site_.Site,
    key_segment: key.KeySegment,
    ctx: StorageContextType,
    default: Value | Empty = None,
) -> Value | Empty:
    """Get metadata value for container at site.

    Args:
        site: Container site
        key_segment: Metadata key
        ctx: Storage context
        default: Default value if not found

    Returns:
        Metadata value or default if doesn't exist

    Raises:
        StorageInterfaceError: If context doesn't support reads
    """
    meta_site = key.join_segment(key.to_meta(site), key_segment)
    value = require_read_context(ctx).get(meta_site)
    if value is EMPTY:
        return default
    return value


def exists_metadata(site: site_.Site, key_segment: key.KeySegment, ctx: StorageContextType) -> bool:
    """Check if metadata key exists for container at site.

    Args:
        site: Container site
        key_segment: Metadata key
        ctx: Storage context

    Returns:
        True if metadata exists

    Raises:
        StorageInterfaceError: If context doesn't support reads
    """
    meta_site = key.join_segment(key.to_meta(site), key_segment)
    return require_read_context(ctx).exists(meta_site)


def delete_metadata(site: site_.Site, key_segment: key.KeySegment, ctx: StorageContextType) -> None:
    """Delete metadata key for container at site.

    Idempotent: silent if metadata doesn't exist.

    Args:
        site: Container site
        key_segment: Metadata key
        ctx: Storage context

    Raises:
        StorageInterfaceError: If context doesn't support writes
    """
    meta_site = key.join_segment(key.to_meta(site), key_segment)
    require_write_context(ctx).delete(meta_site)


def iter_metadata_keys(
    site: site_.Site, ctx: StorageContextType
) -> Generator[key.KeySegment, None, None]:
    """Iterate over metadata keys for container at site.

    Args:
        site: Container site
        ctx: Storage context

    Yields:
        Metadata keys

    Raises:
        StorageInterfaceError: If context doesn't support reads
    """
    from everyshape.storage import LengthFilter, PrefixFilter, StorageScanOptions

    meta_site = key.to_meta(site)
    # Scan immediate children of metadata site only (length = meta_site + 1)
    prefix = PrefixFilter(prefix=meta_site)
    child_len = LengthFilter(length=len(meta_site) + 1)
    options = StorageScanOptions(
        start=(*meta_site, ""),  # Start after meta_site itself
        break_filter=prefix,
        filter=prefix & child_len,
    )
    for meta_key in require_read_context(ctx).scan(options).keys():
        # Extract last segment (metadata key)
        yield meta_key[-1]
