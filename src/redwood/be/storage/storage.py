"""Storage protocol definitions.

Defines the abstract interfaces for storage operations, transactions,
and iteration. Implementations must conform to these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from redwood.abc import TupleKey

    from .transaction import TransactionProtocol
    from .types import SubscriptionCallback, SubscriptionHandle


@runtime_checkable
class StorageProtocol(Protocol):
    """Storage interface with transactions and subscriptions.

    Top-level interface for storage operations. Provides transaction
    management and subscription capabilities.
    """

    # ========================================================================
    # Transaction Management
    # ========================================================================

    def begin(self, *, write: bool = False) -> TransactionProtocol:
        """Begin new transaction.

        Args:
            write: Whether transaction allows writes.

        Returns:
            New transaction instance.

        Raises:
            StorageOperationError: If transaction creation fails.
        """
        ...

    # ========================================================================
    # Subscriptions
    # ========================================================================

    def subscribe(
        self,
        pattern: TupleKey,
        callback: SubscriptionCallback,
    ) -> SubscriptionHandle:
        """Subscribe to key pattern changes.

        Args:
            pattern: Key prefix pattern to match.
            callback: Function called on matching mutations.

        Returns:
            Handle for unsubscribing.

        Raises:
            StorageOperationError: If subscription fails.
        """
        ...

    def unsubscribe(self, handle: SubscriptionHandle) -> None:
        """Unsubscribe from changes.

        Args:
            handle: Subscription handle from subscribe().

        Raises:
            StorageOperationError: If handle invalid or unsubscribe fails.
        """
        ...

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


__all__ = [
    "StorageProtocol",
]
