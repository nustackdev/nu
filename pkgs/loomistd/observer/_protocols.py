from __future__ import annotations

from typing import Any, Protocol

from loomistd.codec import CodecProtocol

from ._types import ObserverCallbackFn, ObserverEncodedKeyT, ObserverKeyT


class ObserverProtocol(Protocol[ObserverKeyT, ObserverEncodedKeyT]):
    """
    Protocol defining state change observation operations.

    Observer implementations handle state change notifications with:
    - Topic-based routing using StorageKeyT (tuple[str, ...])
    - Async notification delivery
    - Proper error handling and validation
    - Type safety through StorageKeyT constraints

    Type Parameters:
        StorageKeyT: Topic type (tuple of strings matching state keys)

    Implementation Requirements:
        - Must validate topic formats
        - Must handle concurrent subscriptions
        - Must guarantee notification delivery
        - Must support pattern matching on topics
    """

    @property
    def codec(self) -> CodecProtocol[ObserverKeyT, Any, ObserverEncodedKeyT, Any]:
        """
        Get codec for encoding/decoding topics.
        """
        ...

    async def connect(self) -> None:
        """
        Establish connection to notification system.

        Raises:
            ObserverConnectionError: If connection fails
        """
        ...

    async def disconnect(self) -> None:
        """
        Close connection to notification system.

        Raises:
            ObserverConnectionError: If disconnection fails
            ObserverError: If cleanup fails
        """
        ...

    async def notify(self, topic: ObserverKeyT) -> None:
        """
        Notify all subscribers of state change.

        Args:
            topic: Topic identifying changed state

        Raises:
            ObserverConnectionError: If not connected
            ObserverOperationError: If notification fails
            ObserverValidationError: If topic invalid
        """
        ...

    async def subscribe(
        self, topic_pattern: ObserverKeyT, callback: ObserverCallbackFn[ObserverKeyT]
    ) -> SubscriptionProtocol[ObserverKeyT]:
        """
        Subscribe to topic pattern.

        Args:
            topic_pattern: Topic pattern to match
            callback: Async callback for notifications

        Returns:
            Subscription for later unsubscribe

        Raises:
            ObserverConnectionError: If not connected
            ObserverValidationError: If topic pattern invalid
        """
        ...

    async def unsubscribe(self, subscription: SubscriptionProtocol[ObserverKeyT]) -> None:
        """
        Remove subscription.

        Args:
            subscription: Subscription to remove

        Raises:
            ObserverConnectionError: If not connected
            ObserverOperationError: If unsubscribe fails
        """
        ...


class SubscriptionProtocol(Protocol[ObserverKeyT]):
    """
    Represents a subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Async callable that will be invoked on matching notifications.
            Must accept a single parameter of type StorageKeyT.

    Type Parameters:
        StorageKeyT: Topic type (tuple of strings)
    """

    @property
    def topic_pattern(self) -> ObserverKeyT:
        """
        Get topic pattern for subscription.
        """
        ...

    @property
    def callback(self) -> ObserverCallbackFn[ObserverKeyT]:
        """
        Get callback for subscription.
        """
        ...
