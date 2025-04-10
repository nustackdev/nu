from __future__ import annotations

from typing import Protocol

from ..types import AsyncStateCallbackFn, StatePath, StatePathComponent, SyncStateCallbackFn
from .kv_storage import (
    AsyncSubscriptionProtocol,
    AsyncTransactionContextManagerProtocol,
    AsyncTransactionProtocol,
    SyncSubscriptionProtocol,
    SyncTransactionContextManagerProtocol,
    SyncTransactionProtocol,
)
from .tree_storage import (
    AsyncStateDictProtocol,
    AsyncStateListProtocol,
    SyncStateDictProtocol,
    SyncStateListProtocol,
)

__all__ = [
    "AsyncStateProtocol",
    "SyncStateProtocol",
]


class AsyncStateProtocol(Protocol):
    """
    Protocol for asynchronous state management.

    This interface defines the contract for state storage implementations,
    providing methods to access dictionary and list nodes in the state tree,
    as well as transaction management.
    """

    async def dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> AsyncStateDictProtocol:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new AsyncStateDictProtocol instance for the nested dictionary node
        """
        ...

    async def list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol | None" = None,
    ) -> AsyncStateListProtocol:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new AsyncStateListProtocol instance for the nested list node
        """
        ...

    async def begin_transaction(self) -> "AsyncTransactionProtocol":
        """
        Begin a new transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    async def transaction(self) -> AsyncTransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager for use in async with statements
        """
        ...

    async def subscribe(
        self,
        key: StatePath,
        callback: AsyncStateCallbackFn,
        depth: int = ...,
    ) -> AsyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Async callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.


        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        ...

    async def unsubscribe(self, subscription: AsyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...


class SyncStateProtocol(Protocol):
    """
    Protocol for synchronous state management.

    This interface defines the contract for state storage implementations,
    providing methods to access dictionary and list nodes in the state tree,
    as well as transaction management.
    """

    def dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> SyncStateDictProtocol:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new SyncStateDictProtocol instance for the nested dictionary node
        """
        ...

    def list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol | None" = None,
    ) -> SyncStateListProtocol:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new SyncStateListProtocol instance for the nested list node
        """
        ...

    def begin_transaction(self) -> "SyncTransactionProtocol":
        """
        Begin a new transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    def transaction(self) -> SyncTransactionContextManagerProtocol:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager for use in with statements
        """
        ...

    def subscribe(
        self,
        key: StatePath,
        callback: SyncStateCallbackFn,
        depth: int = ...,
    ) -> SyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.


        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        ...

    def unsubscribe(self, subscription: SyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        ...
