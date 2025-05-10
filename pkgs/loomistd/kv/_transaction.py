from __future__ import annotations

from loomi.interfaces.state.kv import (
    AsyncTransactionalHandlerProtocol,
    AsyncTransactionContextManagerProtocol,
    AsyncTransactionProtocol,
)

from ._types import StorageValueT

__all__ = [
    "TransactionContextManager",
]


class TransactionContextManager(AsyncTransactionContextManagerProtocol[StorageValueT]):
    """Async context manager for storage transactions."""

    def __init__(self, handler: AsyncTransactionalHandlerProtocol[StorageValueT]):
        """
        Initialize transaction context manager.

        Args:
            storage: Storage instance to manage transactions for
        """
        self.handler = handler
        self.transaction: AsyncTransactionProtocol[StorageValueT] | None = None

    async def __aenter__(self) -> AsyncTransactionProtocol[StorageValueT]:
        """
        Start a new transaction.

        Returns:
            New transaction instance

        Raises:
            StorageError: If transaction cannot be started
        """
        self.transaction = await self.handler.begin_transaction()
        return self.transaction

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Commit or rollback transaction based on context exit.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self.transaction:
            if exc_type is None:
                await self.transaction.commit()
            else:
                await self.transaction.rollback()
