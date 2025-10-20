from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.backends import (
        SnapshotContextManagerProtocol,
        SnapshotHandlerProtocol,
        SnapshotProtocol,
    )


__all__ = [
    "SnapshotContextManager",
]


class SnapshotContextManager:
    """Context manager for storage snapshots."""

    def __init__(self, handler: SnapshotHandlerProtocol) -> None:
        """Initialize snapshot context manager.

        Args:
            handler: Storage instance to manage snapshots for
        """
        self.handler = handler
        self.snapshot: SnapshotProtocol | None = None

    def __enter__(self) -> SnapshotProtocol:
        """Create a new snapshot.

        Returns:
            New snapshot instance

        Raises:
            StorageError: If snapshot cannot be created
        """
        self.snapshot = self.handler.begin_snapshot()
        return self.snapshot

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> bool:
        """Clean up snapshot resources.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.snapshot:
            self.snapshot.close()
        return exc_type is None


if TYPE_CHECKING:
    _: type[SnapshotContextManagerProtocol] = SnapshotContextManager
