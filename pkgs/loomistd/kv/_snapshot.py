from __future__ import annotations

from loomi.behaviors.state.protocols.kv import (
    SyncSnapshotContextManagerProtocol,
    SyncSnapshotHandlerProtocol,
    SyncSnapshotProtocol,
)

from ._types import StorageValueT

__all__ = [
    "SnapshotContextManager",
]


class SnapshotContextManager(SyncSnapshotContextManagerProtocol[StorageValueT]):
    """Sync context manager for storage snapshots."""

    def __init__(self, handler: SyncSnapshotHandlerProtocol[StorageValueT]):
        """
        Initialize snapshot context manager.

        Args:
            handler: Storage instance to manage snapshots for
        """
        self.handler = handler
        self.snapshot: SyncSnapshotProtocol[StorageValueT] | None = None

    def __enter__(self) -> SyncSnapshotProtocol[StorageValueT]:
        """
        Create a new snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot cannot be created
        """
        self.snapshot = self.handler.begin_snapshot()
        return self.snapshot

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Clean up snapshot resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.snapshot:
            self.snapshot.close()
