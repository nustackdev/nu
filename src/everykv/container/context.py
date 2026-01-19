"""Storage context management."""

from __future__ import annotations

from functools import lru_cache

from everykv.storage import (
    ReadAccessProtocol,
    ReadWriteAccessProtocol,
    SnapshotProtocol,
    StorageInterfaceError,
    TransactionProtocol,
    WriteAccessProtocol,
    WriteBatchProtocol,
)


__all__ = [
    "require_read_context",
    "require_readwrite_context",
    "require_snapshot",
    "require_transaction",
    "require_write_batch",
    "require_write_context",
]


@lru_cache(maxsize=2048)
def require_read_context(ctx: object) -> ReadAccessProtocol:
    """Assert that context supports read operations.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to ReadAccessProtocol type

    Raises:
        StorageInterfaceError: If context doesn't support read operations
    """
    if not isinstance(ctx, ReadAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement read access protocol. "
            "This operation requires read access, either a transaction or a snapshot should be used."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_write_context(ctx: object) -> WriteAccessProtocol:
    """Assert that context supports write operations.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to WriteAccessProtocol type

    Raises:
        StorageInterfaceError: If context doesn't support write operations
    """
    if not isinstance(ctx, WriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write access protocol. "
            "This operation requires write access, either a transaction or a write batch should be used."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_readwrite_context(ctx: object) -> ReadWriteAccessProtocol:
    """Assert that context supports both read and write operations.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to ReadAccessProtocol & WriteAccessProtocol type

    Raises:
        StorageInterfaceError: If context doesn't support both protocols
    """
    if not isinstance(ctx, ReadWriteAccessProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement either read or write access protocol. "
            "This operation requires both read and write access, a transaction should be used."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_transaction(ctx: object) -> TransactionProtocol:
    """Assert that context is a transaction.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to TransactionProtocol type

    Raises:
        StorageInterfaceError: If context is not a transaction
    """
    if not isinstance(ctx, TransactionProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement transaction protocol. "
            "This operation requires a Transaction context."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_snapshot(ctx: object) -> SnapshotProtocol:
    """Assert that context is a snapshot.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to SnapshotProtocol type

    Raises:
        StorageInterfaceError: If context is not a snapshot
    """
    if not isinstance(ctx, SnapshotProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement snapshot protocol. "
            "This operation requires a Snapshot context."
        )
    return ctx


@lru_cache(maxsize=2048)
def require_write_batch(ctx: object) -> WriteBatchProtocol:
    """Assert that context is a write batch.

    Args:
        ctx: Storage context to check

    Returns:
        The same context, narrowed to WriteBatchProtocol type

    Raises:
        StorageInterfaceError: If context is not a write batch
    """
    if not isinstance(ctx, WriteBatchProtocol):
        raise StorageInterfaceError(
            f"Context type {type(ctx).__name__} doesn't implement write-batch protocol. "
            "This operation requires a WriteBatch context."
        )
    return ctx
