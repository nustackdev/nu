from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, final

from loomi.interfaces.state.observer import SyncSubscriptionProtocol
from loomistd.codec import CodecProtocol

from ._exceptions import ObserverConnectionError, ObserverValidationError
from ._types import ObserverCallbackFn, ObserverEncodedKeyT, ObserverKeyT

__all__ = [
    "BaseObserver",
    "Subscription",
]


class BaseObserver(ABC, Generic[ObserverKeyT, ObserverEncodedKeyT]):
    """
    Base class for observer implementations.

    Provides core functionality for state change observation with:
    - Connection management
    - Topic validation
    - Thread-safe subscription tracking
    - Sync notification delivery

    Type Parameters:
        ObserverKeyT: Topic type (tuple of strings)
        ObserverEncodedKeyT: Encoded topic type
    """

    codec: CodecProtocol[ObserverKeyT, Any, ObserverEncodedKeyT, Any]

    def setup(self) -> None:
        """
        Service setup called after service initialization.
        """
        self._connected = False
        self.connect()

    def cleanup(self) -> None:
        """
        Service cleanup called after service shutdown.
        """
        self.disconnect()

    def _ensure_connected(self) -> None:
        """
        Verify connection state.

        Raises:
            ObserverConnectionError: If observer not connected
        """
        if not self._connected:
            raise ObserverConnectionError("Observer not connected")

    def _validate_topic(self, topic: ObserverKeyT) -> None:
        """
        Validate topic format.

        Args:
            topic: Topic to validate

        Raises:
            ObserverValidationError: If topic format invalid
        """
        if not isinstance(topic, tuple) or not all(isinstance(x, str) for x in topic):
            raise ObserverValidationError(f"Invalid topic format: {topic}")

    @final
    def connect(self) -> None:
        """
        Connect to notification system.

        Raises:
            ObserverConnectionError: If connection fails
        """
        if self._connected:
            return
        try:
            self._connect_impl()
            self._connected = True
        except Exception as e:
            raise ObserverConnectionError(f"Failed to connect: {e}") from e

    @abstractmethod
    def _connect_impl(self) -> None:
        """Implementation-specific connect logic."""
        raise NotImplementedError

    @final
    def disconnect(self) -> None:
        """
        Disconnect from notification system.

        Raises:
            ObserverConnectionError: If disconnection fails
        """
        if not self._connected:
            return
        try:
            self._disconnect_impl()
        finally:
            self._connected = False

    @abstractmethod
    def _disconnect_impl(self) -> None:
        """Implementation-specific disconnect logic."""
        raise NotImplementedError

    @final
    def notify(self, topic: ObserverKeyT) -> None:
        """
        Notify subscribers of state change.

        Args:
            topic: Topic identifying changed state
        """
        self._ensure_connected()
        self._validate_topic(topic)
        self._notify_impl(topic)

    @abstractmethod
    def _notify_impl(self, topic: ObserverKeyT) -> None:
        """
        Implementation-specific notify logic.

        Args:
            topic: Topic identifying changed state
            subscriptions: List of matching subscriptions
        """
        raise NotImplementedError

    @final
    def subscribe(
        self,
        key: ObserverKeyT,
        callback: ObserverCallbackFn,
        depth: int = 0,
    ) -> SyncSubscriptionProtocol:
        """
        Subscribe to topic pattern.

        Args:
            key: Topic pattern to match
            callback: Sync callback for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.

        Returns:
            New subscription instance
        """
        self._ensure_connected()
        self._validate_topic(key)

        subscription = Subscription(
            key,
            depth,
            callback,
        )

        self._subscribe_impl(subscription)
        return subscription

    @abstractmethod
    def _subscribe_impl(self, subscription: SyncSubscriptionProtocol) -> None:
        """Implementation-specific subscribe logic."""
        raise NotImplementedError

    @final
    def unsubscribe(self, subscription: SyncSubscriptionProtocol) -> None:
        """
        Remove subscription.

        Args:
            subscription: Subscription to remove
        """
        self._ensure_connected()
        self._unsubscribe_impl(subscription)

    @abstractmethod
    def _unsubscribe_impl(self, subscription: SyncSubscriptionProtocol) -> None:
        """Implementation-specific unsubscribe logic."""
        raise NotImplementedError


@dataclass
class Subscription(SyncSubscriptionProtocol, Generic[ObserverKeyT]):
    """
    Represents a subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        depth:
            Get depth of topic pattern matching.
            If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.
        callback:
            Sync callable that will be invoked on matching notifications.
            Must accept a single parameter of type ObserverKey.

    Type Parameters:
        ObserverKey: Topic type (tuple of strings)
    """

    _topic_pattern: ObserverKeyT
    _depth: int
    _callback: ObserverCallbackFn

    @property
    def topic_pattern(self) -> ObserverKeyT:
        return self._topic_pattern

    @property
    def callback(self) -> ObserverCallbackFn:
        return self._callback

    @property
    def depth(self) -> int:
        return self._depth
