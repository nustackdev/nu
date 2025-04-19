from __future__ import annotations

from typing import Protocol, runtime_checkable

from .kv import (
    AsyncTransactionContextManagerProtocol,
    AsyncTransactionProtocol,
    SyncTransactionContextManagerProtocol,
    SyncTransactionProtocol,
)
from .observer import AsyncSubscriptionProtocol, SyncSubscriptionProtocol
from .tree import (
    AsyncTreeDictProtocol,
    AsyncTreeListProtocol,
    SyncTreeDictProtocol,
    SyncTreeListProtocol,
)
from .type_vars import StateValueT
from .types import AsyncCallbackFn, StatePath, StatePathComponent, SyncCallbackFn

__all__ = [
    "AsyncStateProtocol",
    "SyncStateProtocol",
]


@runtime_checkable
class AsyncStateProtocol(Protocol[StateValueT]):
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
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> AsyncTreeDictProtocol[StateValueT]:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new AsyncTreeDictProtocol instance for the nested dictionary node
        """
        ...

    async def list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> AsyncTreeListProtocol[StateValueT]:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new AsyncTreeListProtocol instance for the nested list node
        """
        ...

    async def is_dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> bool:
        """
        Check if the path is a dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path is a dictionary node, False otherwise
        """
        ...

    async def is_list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> bool:
        """
        Check if the path is a list node.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path is a list node, False otherwise
        """
        ...

    async def exists(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> bool:
        """
        Check if the path exists.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path exists, False otherwise
        """
        ...

    async def begin_transaction(self) -> "AsyncTransactionProtocol[StateValueT]":
        """
        Begin a new transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    async def transaction(self) -> AsyncTransactionContextManagerProtocol[StateValueT]:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager for use in async with statements
        """
        ...

    async def subscribe(
        self,
        key: StatePath,
        callback: AsyncCallbackFn,
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


@runtime_checkable
class SyncStateProtocol(Protocol[StateValueT]):
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
        txn: "SyncTransactionProtocol[StateValueT] | None" = None,
    ) -> SyncTreeDictProtocol[StateValueT]:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new SyncTreeDictProtocol instance for the nested dictionary node
        """
        ...

    def list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "SyncTransactionProtocol[StateValueT] | None" = None,
    ) -> SyncTreeListProtocol[StateValueT]:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new SyncTreeListProtocol instance for the nested list node
        """
        ...

    def is_dict(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> bool:
        """
        Check if the path is a dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path is a dictionary node, False otherwise
        """
        ...

    def is_list(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> bool:
        """
        Check if the path is a list node.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path is a list node, False otherwise
        """
        ...

    def exists(
        self,
        path: StatePathComponent,
        /,
        *paths: StatePathComponent,
        txn: "AsyncTransactionProtocol[StateValueT] | None" = None,
    ) -> bool:
        """
        Check if the path exists.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the path exists, False otherwise
        """
        ...

    def begin_transaction(self) -> "SyncTransactionProtocol[StateValueT]":
        """
        Begin a new transaction.

        Returns:
            New transaction instance

        Raises:
            TransactionError: If transaction cannot be started
        """
        ...

    def transaction(self) -> SyncTransactionContextManagerProtocol[StateValueT]:
        """
        Get transaction context manager.

        Returns:
            Transaction context manager for use in with statements
        """
        ...

    def subscribe(
        self,
        key: StatePath,
        callback: SyncCallbackFn,
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
