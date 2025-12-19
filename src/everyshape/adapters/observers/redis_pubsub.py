"""Redis pub/sub observer implementation for inter-process notification.

The RedisObserver provides distributed notification across processes using Redis
pub/sub. When a key changes in one process, all other processes subscribed via
Redis will receive the notification.

Features:
- Inter-process notification via Redis pub/sub
- Thread-safe subscription management (inherited from BaseObserver)
- Automatic reconnection on connection loss
- Configurable channel prefix
"""

from __future__ import annotations

import json
import threading
from logging import getLogger
from typing import TYPE_CHECKING, Any

from ._base import BaseObserver


if TYPE_CHECKING:
    from logging import Logger

    from everyshape.loc import key
    from everyshape.storage import CodecProtocol, ObserverProtocol


logger: Logger = getLogger(__name__)


__all__ = [
    "RedisObserver",
]


class RedisObserver(BaseObserver[str]):
    """Redis pub/sub observer for inter-process notifications.

    Uses Redis pub/sub to broadcast key change notifications across multiple
    processes. Each process subscribes to a Redis channel and receives
    notifications when keys change in any connected process.

    The observer uses a background listener thread to receive messages from
    Redis and dispatch them to local subscriptions.

    Args:
        codec: Codec for encoding/decoding keys.
        redis_url: Redis connection URL (default: redis://localhost:6379).
        channel_prefix: Prefix for Redis channel names (default: everyshape).
        notify_self: Whether to notify local subscriptions when this process
            publishes (default: True). Set to False if notifications are already
            handled locally before publishing.

    Examples:
        >>> from everyshape.storage.observer.subscription import (
        ...     PrefixFilter,
        ...     SubscriptionOptions,
        ... )

        >>> # Process 1: Create observer and subscribe
        >>> observer = RedisObserver(codec, redis_url="redis://localhost:6379")
        >>> observer.connect()
        >>> sub = observer.subscribe(
        ...     SubscriptionOptions(filter=PrefixFilter(prefix=("users",)))
        ... )
        >>> sub.bind(lambda key: print(f"Process 1 received: {key}"))

        >>> # Process 2: Notify changes
        >>> observer2 = RedisObserver(codec, redis_url="redis://localhost:6379")
        >>> observer2.connect()
        >>> observer2.notify(("users", "alice"))  # Both processes receive this

        >>> # Cleanup
        >>> observer.disconnect()
        >>> observer2.disconnect()
    """

    def __init__(
        self,
        codec: CodecProtocol[str, Any],
        *,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "everyshape",
        notify_self: bool = True,
    ) -> None:
        """Initialize Redis observer.

        Args:
            codec: Codec for encoding/decoding keys.
            redis_url: Redis connection URL.
            channel_prefix: Prefix for Redis pub/sub channels.
            notify_self: Whether to process notifications from self.
        """
        super().__init__(codec)
        self._redis_url = redis_url
        self._channel_prefix = channel_prefix
        self._notify_self = notify_self
        self._channel = f"{channel_prefix}:notifications"

        # Redis connections (will be created on connect)
        self._redis_pub: Any = None  # For publishing
        self._redis_sub: Any = None  # For subscribing
        self._pubsub: Any = None

        # Listener thread
        self._listener_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Instance ID for filtering self-notifications
        self._instance_id = id(self)

    def _connect_impl(self) -> None:
        """Connect to Redis and start listener thread.

        Creates separate Redis connections for publishing and subscribing,
        subscribes to the notification channel, and starts the listener thread.

        Raises:
            ImportError: If redis package is not installed.
            ConnectionError: If Redis connection fails.
        """
        try:
            import redis
        except ImportError as e:
            raise ImportError(
                "redis package is required for RedisObserver. Install it with: pip install redis"
            ) from e

        # Create Redis connections
        self._redis_pub = redis.from_url(self._redis_url)
        self._redis_sub = redis.from_url(self._redis_url)

        # Test connection
        self._redis_pub.ping()

        # Subscribe to notification channel
        self._pubsub = self._redis_sub.pubsub()
        self._pubsub.subscribe(self._channel)

        # Start listener thread
        self._stop_event.clear()
        self._listener_thread = threading.Thread(
            target=self._listener_loop,
            name=f"RedisObserver-{self._instance_id}",
            daemon=True,
        )
        self._listener_thread.start()

        logger.info("Connected to Redis at %s, channel: %s", self._redis_url, self._channel)

    def _disconnect_impl(self) -> None:
        """Disconnect from Redis and stop listener thread.

        Stops the listener thread, unsubscribes from channels, and closes
        Redis connections.
        """
        # Signal listener to stop
        self._stop_event.set()

        # Wait for listener thread to stop
        if self._listener_thread is not None and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2.0)
            self._listener_thread = None

        # Cleanup pub/sub
        if self._pubsub is not None:
            try:
                self._pubsub.unsubscribe()
                self._pubsub.close()
            except Exception as e:
                logger.warning("Error closing pubsub: %s", e)
            self._pubsub = None

        # Close Redis connections
        if self._redis_sub is not None:
            try:
                self._redis_sub.close()
            except Exception as e:
                logger.warning("Error closing subscriber connection: %s", e)
            self._redis_sub = None

        if self._redis_pub is not None:
            try:
                self._redis_pub.close()
            except Exception as e:
                logger.warning("Error closing publisher connection: %s", e)
            self._redis_pub = None

        logger.info("Disconnected from Redis")

    def _notify_impl(self, topic: key.Key) -> None:
        """Publish notification to Redis and optionally notify locally.

        Publishes the key change to Redis channel. If notify_self is True,
        also notifies local subscriptions immediately.

        Args:
            topic: Key that changed.
        """
        # Prepare message
        message = json.dumps(
            {
                "instance_id": self._instance_id,
                "key": topic,
            }
        )

        # Publish to Redis
        if self._redis_pub is not None:
            try:
                self._redis_pub.publish(self._channel, message)
            except Exception as e:
                logger.error("Failed to publish to Redis: %s", e)

        # Notify locally if configured (for the local publisher)
        if self._notify_self:
            self._notify_local(topic)

    def _notify_local(self, topic: key.Key) -> None:
        """Notify local subscriptions without publishing to Redis.

        Args:
            topic: Key that changed.
        """
        if self._registry is None:
            return

        # Find matching subscriptions (thread-safe)
        matching = self._registry.match(topic)

        # Execute callbacks outside any locks
        for subscription in matching:
            for error in subscription.notify(topic):
                logger.error("Callback failed for %s: %s", topic, error)

    def _listener_loop(self) -> None:
        """Background thread that listens for Redis messages.

        Continuously listens for messages on the subscribed channel and
        dispatches notifications to local subscriptions.
        """
        logger.debug("Redis listener started for channel: %s", self._channel)

        while not self._stop_event.is_set():
            try:
                # Get message with timeout to allow checking stop event
                message = self._pubsub.get_message(timeout=0.1)

                if message is None:
                    continue

                # Skip subscription confirmation messages
                if message["type"] != "message":
                    continue

                # Parse message
                try:
                    raw_data = message["data"]
                    # Redis returns bytes, decode if needed
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")
                    data = json.loads(raw_data)
                    sender_id = data.get("instance_id")
                    key_tuple = tuple(data["key"])

                    # Skip self-notifications if notify_self is True
                    # (they were already handled in _notify_impl)
                    if sender_id == self._instance_id and self._notify_self:
                        continue

                    # Notify local subscriptions
                    self._notify_local(key_tuple)

                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning("Invalid message received: %s, error: %s", message, e)

            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error("Error in listener loop: %s", e)
                    # Brief pause before retrying
                    self._stop_event.wait(0.5)

        logger.debug("Redis listener stopped")


if TYPE_CHECKING:
    _: type[ObserverProtocol[str]] = RedisObserver
