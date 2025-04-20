from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from pydantic import Field

from loomi.declarative import Attach
from loomi.interfaces.state.observer import AsyncObservableProtocol, AsyncSubscriptionProtocol
from loomi.service import AsyncService
from loomi.spec import Spec
from loomistd.codec import CodecProtocol
from loomistd.codec.passthrough import PassthroughCodec

from .._base import BaseObserver, BaseObserverSpec
from .logger import logger
from .types import InMemoryObserverEncodedKey, InMemoryObserverKey

__all__ = [
    "InMemoryObserverSpec",
    "InMemoryObserver",
]


class InMemoryObserverSpec(BaseObserverSpec):
    codec: Spec = Field(default=Spec(factory=PassthroughCodec))


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

        self._subscriptions: dict[InMemoryObserverKey, list[AsyncSubscriptionProtocol]] = {}

    async def _disconnect_impl(self) -> None:
        async with self._data_lock:
            self._subscriptions.clear()

    def _matches_pattern(
        self,
        topic: InMemoryObserverKey,
        pattern: InMemoryObserverKey,
        depth: int,
    ) -> bool:
        if len(topic) < len(pattern):
            return False

        if depth != -1 and len(topic) - len(pattern) != depth:
            return False

        return all(p == "*" or t == p for t, p in zip(topic, pattern))

    async def _notify_impl(self, topic: InMemoryObserverKey) -> None:
        async with self._data_lock:
            matching_subs = []
            for pattern, subs in self._subscriptions.items():
                if self._matches_pattern(topic, pattern, -1):
                    matching_subs.extend(subs)

        # Execute callbacks outside lock
        for sub in matching_subs:
            # Check if the subscription matches the topic with the specified depth
            if not self._matches_pattern(topic, sub.topic_pattern, sub.depth):
                continue

            try:
                await sub.callback(topic)
            except Exception as e:
                logger.error(f"Callback failed for {topic}: {e}")

    async def _subscribe_impl(self, subscription: AsyncSubscriptionProtocol) -> None:
        topic_pattern = subscription.topic_pattern
        async with self._data_lock:
            if topic_pattern not in self._subscriptions:
                self._subscriptions[topic_pattern] = []
            self._subscriptions[topic_pattern].append(subscription)

    async def _unsubscribe_impl(self, subscription: AsyncSubscriptionProtocol) -> None:
        async with self._data_lock:
            if subscription.topic_pattern in self._subscriptions:
                subs = self._subscriptions[subscription.topic_pattern]
                subs = [s for s in subs if s != subscription]
                if subs:
                    self._subscriptions[subscription.topic_pattern] = subs
                else:
                    del self._subscriptions[subscription.topic_pattern]


if TYPE_CHECKING:
    _: type[AsyncObservableProtocol] = InMemoryObserver
