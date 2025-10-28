from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.be import (
        SnapshotContextManagerProtocol,
        SnapshotHandlerProtocol,
        SnapshotProtocol,
        TransactionalHandlerProtocol,
        TransactionContextManagerProtocol,
        TransactionProtocol,
    )


__all__ = [
    "SnapshotContextManager",
    "TransactionContextManager",
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


class TransactionContextManager:
    """Context manager for storage transactions."""

    def __init__(self, handler: TransactionalHandlerProtocol) -> None:
        """Initialize transaction context manager.

        Args:
            handler: Transactional handler to manage transactions
        """
        self.handler = handler
        self.transaction: TransactionProtocol | None = None

    def __enter__(self) -> TransactionProtocol:
        """Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        self.transaction = self.handler.begin_transaction()
        return self.transaction

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> bool:
        """Commit or rollback transaction based on context exit.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.transaction:
            if exc_type is None:
                self.transaction.commit()
                return True
            else:
                self.transaction.rollback()
                return False
        return exc_type is None


if TYPE_CHECKING:
    _: type[TransactionContextManagerProtocol] = TransactionContextManager
    __: type[SnapshotContextManagerProtocol] = SnapshotContextManager
