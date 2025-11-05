"""Storage protocol definitions.

Defines the abstract interfaces for storage operations, transactions,
and iteration. Implementations must conform to these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from .transaction import TransactionalStorageProtocol


if TYPE_CHECKING:
    from redwood.abc import CallbackFn, TupleKey
    from redwood.be.observer import SubscriptionProtocol


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

    def subscribe(
        self,
        pattern: TupleKey,
        callback: CallbackFn,
        depth: int = 0,
    ) -> SubscriptionProtocol:
        """Subscribe to key pattern changes.

        Args:
            pattern: Key prefix pattern to match.
            callback: Function called on matching mutations.
            depth: Depth of pattern matching (0=exact, 1=prefix, -1=all subkeys).

        Returns:
            Handle for unsubscribing.

        Raises:
            StorageOperationError: If subscription fails.
        """
        ...

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from changes.

        Args:
            subscription: Subscription object from subscribe().

        Raises:
            StorageOperationError: If subscription is invalid or unsubscribe fails.
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
