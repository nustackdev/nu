"""Storage protocol definitions.

Defines the abstract interfaces for storage operations, transactions,
and iteration. Implementations must conform to these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .transaction import TransactionalStorageProtocol


if TYPE_CHECKING:
    from everyshape.storage.observer.subscription import Subscription, SubscriptionOptions


@runtime_checkable
class StorageProtocol(TransactionalStorageProtocol, Protocol):
    """Storage interface with transactions and subscriptions.

    Top-level interface for storage operations. Provides transaction
    management and subscription capabilities.
    """

    # ========================================================================
    # Lifecycle
    # ========================================================================

    def open(self) -> None:
        """Open storage and initialize resources.

        Raises:
            StorageOperationError: If open fails.
        """
        ...

    def close(self) -> None:
        """Close storage and release resources.

        All transactions must be completed before closing.

        Raises:
            StorageOperationError: If close fails.
        """
        ...

    # ========================================================================
    # Subscriptions
    # ========================================================================

    def subscribe(self, options: SubscriptionOptions) -> Subscription:
        """Subscribe to key changes with flexible filtering.

        This is the new subscription API that provides:
        - Flexible filtering (prefix, suffix, wildcard, length, composite)
        - Decoupled subscriptions from callbacks
        - Efficient pattern matching

        Args:
            options: Subscription options including filter specification.

        Returns:
            Subscription object for binding callbacks and managing lifecycle.

        Raises:
            StorageOperationError: If subscription fails.

        Examples:
            >>> from everyshape.storage.observer.subscription import (
            ...     PrefixFilter,
            ...     SubscriptionOptions,
            ... )

            >>> # Subscribe to all keys under "users"
            >>> sub = storage.subscribe(
            ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
            ... )
            >>> sub.bind(lambda key: print(f"Changed: {key}"))

            >>> # Use context manager for temporary binding
            >>> with sub(my_callback):
            ...     # Callback is bound during this block
            ...     pass

            >>> # Close when done
            >>> sub.close()
        """
        ...

    # ========================================================================
    # Transaction Management
    # ------------------------------------------------------------------------
    # Transaction management methods are inherited from TransactionalStorageProtocol.
    # begin() -> TransactionProtocol | SnapshotProtocol | WriteBatchProtocol
    # ========================================================================


__all__ = [
    "StorageProtocol",
]
