from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from loomi.attr import UseService
from loomi.interfaces.state.observer import SyncObservableProtocol, SyncSubscriptionProtocol
from loomi.service import SyncService
from loomi.spec import Spec, SpecField
from loomistd.codec import CodecProtocol
from loomistd.codec.passthrough import PassthroughCodec

from .._base import BaseObserver
from .logger import logger
from .types import InMemoryObserverEncodedKey, InMemoryObserverKey

__all__ = [
    "InMemoryObserverSpec",
    "InMemoryObserver",
]


class InMemoryObserver(
    BaseObserver[
        InMemoryObserverKey,
        InMemoryObserverEncodedKey,
    ],
    SyncService,
):
    """In-memory observer with thread-safe subscription management."""

    codec_srv: CodecProtocol[InMemoryObserverKey, Any, InMemoryObserverEncodedKey, Any] = (
        UseService()
    )

    def _connect_impl(self) -> None:
        if not hasattr(self, "_data_lock"):
            self._data_lock: threading.Lock = threading.Lock()

        self._subscriptions: dict[InMemoryObserverKey, list[SyncSubscriptionProtocol]] = {}

    def _disconnect_impl(self) -> None:
        with self._data_lock:
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

    def _notify_impl(self, topic: InMemoryObserverKey) -> None:
        with self._data_lock:
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
                sub.callback(topic)
            except Exception as e:
                logger.error(f"Callback failed for {topic}: {e}")

    def _subscribe_impl(self, subscription: SyncSubscriptionProtocol) -> None:
        topic_pattern = subscription.topic_pattern
        with self._data_lock:
            if topic_pattern not in self._subscriptions:
                self._subscriptions[topic_pattern] = []
            self._subscriptions[topic_pattern].append(subscription)

    def _unsubscribe_impl(self, subscription: SyncSubscriptionProtocol) -> None:
        with self._data_lock:
            if subscription.topic_pattern in self._subscriptions:
                subs = self._subscriptions[subscription.topic_pattern]
                subs = [s for s in subs if s != subscription]
                if subs:
                    self._subscriptions[subscription.topic_pattern] = subs
                else:
                    del self._subscriptions[subscription.topic_pattern]


class InMemoryObserverSpec(Spec):
    name: str = "in_memory_observer"
    factory: type = SpecField(default=InMemoryObserver)
    codec_srv: Spec = SpecField(default=Spec(factory=PassthroughCodec))


if TYPE_CHECKING:
    _: type[SyncObservableProtocol] = InMemoryObserver
