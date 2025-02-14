from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, final

from pydantic import Field

from loomi.service import Spec
from loomistd.codec import CodecProtocol

from ._exceptions import ObserverConnectionError, ObserverValidationError
from ._protocols import SubscriptionProtocol
from ._types import ObserverCallbackFn, ObserverEncodedKeyT, ObserverKeyT


class BaseObserverSpec(Spec):
    """Base observer spec."""

    codec: Spec = Field(default_factory=Spec)

    @classmethod
    def identity_fields(cls) -> set[str]:
        return {"codec"}


class BaseObserver(ABC, Generic[ObserverKeyT, ObserverEncodedKeyT]):
    """
    Base class for observer implementations.

    Provides core functionality for state change observation with:
    - Connection management
    - Topic validation
    - Thread-safe subscription tracking
    - Async notification delivery

    Type Parameters:
        ObserverKeyT: Topic type (tuple of strings)
        ObserverEncodedKeyT: Encoded topic type
    """

    _codec: CodecProtocol[ObserverKeyT, Any, ObserverEncodedKeyT, Any]

    @property
    def codec(self) -> CodecProtocol[ObserverKeyT, Any, ObserverEncodedKeyT, Any]:
        """
        Get codec for encoding/decoding topics.

        Returns:
            Codec instance
        """
        return self._codec

    async def setup(self) -> None:
        """
        Service setup called after service initialization.
        """
        self._connected = False
        await self.connect()

    async def cleanup(self) -> None:
        """
        Service cleanup called after service shutdown.
        """
        await self.disconnect()

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
    async def connect(self) -> None:
        """
        Connect to notification system.

        Raises:
            ObserverConnectionError: If connection fails
        """
        if self._connected:
            return
        try:
            await self._connect_impl()
            self._connected = True
        except Exception as e:
            raise ObserverConnectionError(f"Failed to connect: {e}") from e

    @abstractmethod
    async def _connect_impl(self) -> None:
        """Implementation-specific connect logic."""
        raise NotImplementedError

    @final
    async def disconnect(self) -> None:
        """
        Disconnect from notification system.

        Raises:
            ObserverConnectionError: If disconnection fails
        """
        if not self._connected:
            return
        try:
            await self._disconnect_impl()
        finally:
            self._connected = False

    @abstractmethod
    async def _disconnect_impl(self) -> None:
        """Implementation-specific disconnect logic."""
        raise NotImplementedError

    @final
    async def notify(self, topic: ObserverKeyT) -> None:
        """
        Notify subscribers of state change.

        Args:
            topic: Topic identifying changed state
        """
        self._ensure_connected()
        self._validate_topic(topic)
        await self._notify_impl(topic)

    @abstractmethod
    async def _notify_impl(self, topic: ObserverKeyT) -> None:
        """
        Implementation-specific notify logic.

        Args:
            topic: Topic identifying changed state
            subscriptions: List of matching subscriptions
        """
        raise NotImplementedError

    @final
    async def subscribe(
        self, topic_pattern: ObserverKeyT, callback: ObserverCallbackFn[ObserverKeyT]
    ) -> Subscription[ObserverKeyT]:
        """
        Subscribe to topic pattern.

        Args:
            topic_pattern: Topic pattern to match
            callback: Async callback for notifications

        Returns:
            New subscription instance
        """
        self._ensure_connected()
        self._validate_topic(topic_pattern)

        subscription = Subscription(topic_pattern, callback)

        await self._subscribe_impl(subscription)
        return subscription

    @abstractmethod
    async def _subscribe_impl(self, subscription: Subscription[ObserverKeyT]) -> None:
        """Implementation-specific subscribe logic."""
        raise NotImplementedError

    @final
    async def unsubscribe(self, subscription: Subscription[ObserverKeyT]) -> None:
        """
        Remove subscription.

        Args:
            subscription: Subscription to remove
        """
        self._ensure_connected()
        await self._unsubscribe_impl(subscription)

    @abstractmethod
    async def _unsubscribe_impl(self, subscription: Subscription[ObserverKeyT]) -> None:
        """Implementation-specific unsubscribe logic."""
        raise NotImplementedError


@dataclass
class Subscription(SubscriptionProtocol[ObserverKeyT]):
    """
    Represents a subscription to a topic pattern.

    Attributes:
        topic_pattern:
            Topic pattern to match against notifications.
            Must be a tuple of strings matching state keys.
        callback:
            Async callable that will be invoked on matching notifications.
            Must accept a single parameter of type ObserverKeyT.

    Type Parameters:
        ObserverKeyT: Topic type (tuple of strings)
    """

    _topic_pattern: ObserverKeyT
    _callback: ObserverCallbackFn[ObserverKeyT]

    @property
    def topic_pattern(self) -> ObserverKeyT:
        return self._topic_pattern

    @property
    def callback(self) -> ObserverCallbackFn[ObserverKeyT]:
        return self._callback
