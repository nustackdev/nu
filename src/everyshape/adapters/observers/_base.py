"""Observer base implementation.

Provides the base class for observer implementations with:
- Connection management
- Thread-safe subscription tracking
- Efficient pattern matching via SubscriptionRegistry
- Both new and legacy subscription APIs
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING, Any, Self, final

from everyshape.storage import ObserverConnectionError
from everyshape.storage.observer.registry import SubscriptionRegistry
from everyshape.storage.observer.subscription import (
    Subscription,
    SubscriptionOptions,
)


if TYPE_CHECKING:
    from types import TracebackType

    from everyshape.loc import key
    from everyshape.storage import CodecProtocol


logger = getLogger(__name__)


__all__ = [
    "BaseObserver",
]


class BaseObserver[EncodedKeyT](ABC):
    """Base class for observer implementations.

    Provides core functionality for state change observation with:
    - Connection management
    - Topic validation
    - Thread-safe subscription tracking via SubscriptionRegistry
    - Sync notification delivery
    - Support for both new and legacy subscription APIs

    Type Parameters:
        EncodedKeyT: Encoded topic type (e.g., str for in-memory, bytes for RocksDB)
    """

    def __init__(self, codec: CodecProtocol[EncodedKeyT, Any]) -> None:
        """Initialize observer.

        Args:
            codec: Codec for encoding/decoding topics.
        """
        self._codec = codec
        self._connected: bool = False
        self._registry: SubscriptionRegistry | None = None

    @property
    def codec(self) -> CodecProtocol[EncodedKeyT, Any]:
        """Get codec for encoding/decoding topics."""
        return self._codec

    def _ensure_connected(self) -> None:
        """Verify connection state.

        Raises:
            ObserverConnectionError: If observer not connected.
        """
        if not self._connected:
            raise ObserverConnectionError("Observer not connected")

    @final
    def connect(self) -> None:
        """Connect to notification system.

        Initializes the subscription registry.

        Raises:
            ObserverConnectionError: If connection fails.
        """
        if self._connected:
            return
        try:
            self._registry = SubscriptionRegistry()
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

        Clears all subscriptions.

        Raises:
            ObserverConnectionError: If disconnection fails.
        """
        if not self._connected:
            return
        try:
            self._disconnect_impl()
        finally:
            if self._registry is not None:
                self._registry.clear()
                self._registry = None
            self._connected = False

    @abstractmethod
    def _disconnect_impl(self) -> None:
        """Implementation-specific disconnect logic."""
        raise NotImplementedError

    @final
    def notify(self, topic: key.Key) -> None:
        """Notify subscribers of state change.

        Uses the subscription registry for efficient matching.

        Args:
            topic: Topic identifying changed state.
        """
        self._ensure_connected()
        self._notify_impl(topic)

    def _notify_impl(self, topic: key.Key) -> None:
        """Default notification implementation using registry.

        Finds matching subscriptions and delivers notifications.

        Args:
            topic: Topic identifying changed state.
        """
        if self._registry is None:
            return

        # Find matching subscriptions (thread-safe)
        matching = self._registry.match(topic)

        # Execute callbacks outside any locks
        for subscription in matching:
            for error in subscription.notify(topic):
                logger.error("Callback failed for %s: %s", topic, error)

    @final
    def subscribe(self, options: SubscriptionOptions) -> Subscription:
        """Subscribe to key changes with flexible filtering.

        Args:
            options: Subscription options including filter specification.

        Returns:
            Subscription object for binding callbacks and managing lifecycle.
        """
        self._ensure_connected()

        subscription = Subscription(
            _options=options,
            _observer=self,
        )

        if self._registry is not None:
            self._registry.add(subscription)

        return subscription

    def _close_subscription(self, subscription: Subscription) -> None:
        """Internal method to close a subscription.

        Called by Subscription.close() to remove subscription from registry.

        Args:
            subscription: Subscription to close.
        """
        if self._registry is not None:
            self._registry.remove(subscription)

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
