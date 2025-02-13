from __future__ import annotations

import asyncio
from typing import Any

from ecosystem.std.codec import CodecProtocol
from ecosystem.std.codec.passthrough import PassthroughCodec
from scriptable.service import AsyncService, Attach

from .._base import BaseObserver, BaseObserverSpec, Subscription
from .logger import logger
from .types import InMemoryObserverEncodedKey, InMemoryObserverKey


class InMemoryObserverSpec(BaseObserverSpec):
    pass


class InMemoryObserver(
    BaseObserver[
        InMemoryObserverKey,
        InMemoryObserverEncodedKey,
    ],
    AsyncService,
):
    """In-memory observer with thread-safe subscription management."""

    _codec: CodecProtocol[InMemoryObserverKey, Any, InMemoryObserverEncodedKey, Any] = Attach(
        PassthroughCodec
    )

    async def _connect_impl(self) -> None:
        if not hasattr(self, "_data_lock"):
            self._data_lock: asyncio.Lock = asyncio.Lock()

        self._subscriptions: dict[InMemoryObserverKey, list[Subscription[InMemoryObserverKey]]] = {}

    async def _disconnect_impl(self) -> None:
        async with self._data_lock:
            self._subscriptions.clear()

    def _matches_pattern(self, topic: InMemoryObserverKey, pattern: InMemoryObserverKey) -> bool:
        if len(topic) < len(pattern):
            return False
        return all(p == "*" or t == p for t, p in zip(topic, pattern))

    async def _notify_impl(self, topic: InMemoryObserverKey) -> None:
        async with self._data_lock:
            matching_subs = []
            for pattern, subs in self._subscriptions.items():
                if self._matches_pattern(topic, pattern):
                    matching_subs.extend(subs)

        # Execute callbacks outside lock
        for sub in matching_subs:
            try:
                await sub.callback(topic)
            except Exception as e:
                logger.error(f"Callback failed for {topic}: {e}")

    async def _subscribe_impl(self, subscription: Subscription[InMemoryObserverKey]) -> None:
        topic_pattern = subscription.topic_pattern
        async with self._data_lock:
            if topic_pattern not in self._subscriptions:
                self._subscriptions[topic_pattern] = []
            self._subscriptions[topic_pattern].append(subscription)

    async def _unsubscribe_impl(self, subscription: Subscription[InMemoryObserverKey]) -> None:
        async with self._data_lock:
            if subscription.topic_pattern in self._subscriptions:
                subs = self._subscriptions[subscription.topic_pattern]
                subs = [s for s in subs if s != subscription]
                if subs:
                    self._subscriptions[subscription.topic_pattern] = subs
                else:
                    del self._subscriptions[subscription.topic_pattern]
