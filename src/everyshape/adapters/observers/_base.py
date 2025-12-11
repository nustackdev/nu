"""Observer base."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Any, Self, final

from everyshape.storage import ObserverConnectionError


if TYPE_CHECKING:
    from types import TracebackType

    from everyshape.loc import key
    from everyshape.storage import (
        CallbackFn,
        CodecProtocol,
        SubscriptionProtocol,
    )


logger = getLogger(__name__)


__all__ = [
    "BaseObserver",
    "Subscription",
]


class BaseObserver[EncodedKeyT](ABC):
    """Base class for observer implementations.

    Provides core functionality for state change observation with:
    - Connection management
    - Topic validation
    - Thread-safe subscription tracking
    - Sync notification delivery

    Type Parameters:
        Key: Topic type (tuple of strings)
        ObserverEncodedKeyT: Encoded topic type
    """

    def __init__(self, codec: CodecProtocol[EncodedKeyT, Any]) -> None:
        """Initialize observer.

        Args:
            codec: Codec for encoding/decoding topics
        """
        self._codec = codec
        self._connected: bool = False

    @property
    def codec(self) -> CodecProtocol[EncodedKeyT, Any]:
        """Codec."""
        return self._codec

    def _ensure_connected(self) -> None:
        """Verify connection state.

        Raises:
            ObserverConnectionError: If observer not connected
        """
        if not self._connected:
            raise ObserverConnectionError("Observer not connected")

    @final
    def connect(self) -> None:
        """Connect to notification system.

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
        """Disconnect from notification system.

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
    def notify(self, topic: key.Key) -> None:
        """Notify subscribers of state change.

        Args:
            topic: Topic identifying changed state
        """
        self._ensure_connected()
        self._notify_impl(topic)

    @abstractmethod
    def _notify_impl(self, topic: key.Key) -> None:
        """Implementation-specific notify logic.

        Args:
            topic: Topic identifying changed state
            subscriptions: List of matching subscriptions
        """
        raise NotImplementedError

    @final
    def subscribe(
        self,
        prefix: key.Key,
        callback: CallbackFn,
        prefix_depth: int = 0,
    ) -> SubscriptionProtocol:
        """Subscribe to topic pattern.

        Args:
            prefix: Topic pattern to match
            callback: Sync callback for notifications
            prefix_depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.

        Returns:
            New subscription instance
        """
        self._ensure_connected()

        subscription = Subscription(
            prefix,
            prefix_depth,
            callback,
        )

        self._subscribe_impl(subscription)
        return subscription

    @abstractmethod
    def _subscribe_impl(self, subscription: SubscriptionProtocol) -> None:
        """Implementation-specific subscribe logic."""
        raise NotImplementedError

    @final
    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Remove subscription.

        Args:
            subscription: Subscription to remove
        """
        self._ensure_connected()
        self._unsubscribe_impl(subscription)

    @abstractmethod
    def _unsubscribe_impl(self, subscription: SubscriptionProtocol) -> None:
        """Implementation-specific unsubscribe logic."""
        raise NotImplementedError

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager."""
        self.disconnect()


@dataclass
class Subscription:
    """Represents a subscription to a topic pattern.

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

    _prefix: key.Key
    _prefix_depth: int
    _callback: CallbackFn

    @property
    def prefix(self) -> key.Key:
        """Prefix access."""
        return self._prefix

    @property
    def callback(self) -> CallbackFn:
        """Callback access."""
        return self._callback

    @property
    def prefix_depth(self) -> int:
        """prefix_depth access."""
        return self._prefix_depth
