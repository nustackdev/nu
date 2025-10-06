from __future__ import annotations

from loomi.tree import (
    TransactionalHandlerProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)

from ._types import ValueT

__all__ = [
    "TransactionContextManager",
]


class TransactionContextManager(TransactionContextManagerProtocol[ValueT]):
    """Context manager for storage transactions."""

    def __init__(self, handler: TransactionalHandlerProtocol[ValueT]):
        """
        Initialize transaction context manager.

        Args:
            storage: Storage instance to manage transactions for
        """
        self.handler = handler
        self.transaction: TransactionProtocol[ValueT] | None = None

    def __enter__(self) -> TransactionProtocol[ValueT]:
        """
        Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        self.transaction = self.handler.begin_transaction()
        return self.transaction

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Commit or rollback transaction based on context exit.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.transaction:
            if exc_type is None:
                self.transaction.commit()
            else:
                self.transaction.rollback()
