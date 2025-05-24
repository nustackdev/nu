from __future__ import annotations

from typing import Any, Protocol

from .types import AsyncCallbackFn, ObserverKey, SyncCallbackFn

__all__ = [
    "AsyncObservableProtocol",
    "SyncObservableProtocol",
    "AsyncSubscriptionProtocol",
    "SyncSubscriptionProtocol",
]


class AsyncObservableProtocol(Protocol):
    """Protocol for asynchronous observable state adapters."""

    async def subscribe(
        self,
        topic_pattern: ObserverKey,
        callback: AsyncCallbackFn,
        depth: int = ...,
    ) -> AsyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            topic_pattern: Key prefix to subscribe to
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

    def __hash__(self) -> int:
        """
        Get hash of the observer.

        Returns:
            Hash value of the observer
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """
        Check equality of the observer.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class SyncObservableProtocol(Protocol):
    """Protocol for synchronous observable adapters."""

    def subscribe(
        self,
        key: ObserverKey,
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

    def __hash__(self) -> int:
        """
        Get hash of the observer.

        Returns:
            Hash value of the observer
        """
        ...

    def __eq__(self, other: Any) -> bool:
        """
        Check equality of the observer.

        Args:
            value: Value to compare with

        Returns:
            True if equal, False otherwise
        """
        ...


class AsyncSubscriptionProtocol(Protocol):
    """
    Represents an asynchronous subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Async callable that will be invoked on matching notifications.
            Must accept a single parameter of type StorageValueT.

    Type Parameters:
        StorageValueT: Topic type (tuple of strings)
    """

    @property
    def topic_pattern(self) -> ObserverKey:
        """
        Get topic pattern for subscription.
        """
        ...

    @property
    def callback(self) -> AsyncCallbackFn:
        """
        Get callback for subscription.
        """
        ...

    @property
    def depth(self) -> int:
        """
        Get depth of subscription.
        """
        ...


class SyncSubscriptionProtocol(Protocol):
    """
    Represents a synchronous subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Callable that will be invoked on matching notifications.
            Must accept a single parameter of type StorageValueT.

    Type Parameters:
        StorageValueT: Topic type (tuple of strings)
    """

    @property
    def topic_pattern(self) -> ObserverKey:
        """
        Get topic pattern for subscription.
        """
        ...

    @property
    def callback(self) -> SyncCallbackFn:
        """
        Get callback for subscription.
        """
        ...

    @property
    def depth(self) -> int:
        """
        Get depth for subscription.
        """
        ...
