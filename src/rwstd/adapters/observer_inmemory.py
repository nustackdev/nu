"""In-memory observer implementation with thread-safe subscription management."""

from __future__ import annotations

import threading
from logging import getLogger
from typing import TYPE_CHECKING

import attrs
from mesh import Attach, ResourceSpec, Spec, SyncResource

from .bases import BaseObserver


if TYPE_CHECKING:
    from logging import Logger

    from redwood.abc import TupleKey
    from redwood.be import (
        KeyCodecProtocol,
        ObserverProtocol,
        SubscriptionProtocol,
    )


logger: Logger = getLogger(__name__)


__all__ = [
    "InMemoryObserver",
    "InMemoryObserverSpec",
]


class InMemoryObserver(
    BaseObserver[str],
    SyncResource,
):
    """In-memory observer with thread-safe subscription management."""

    codec: KeyCodecProtocol[str] = Attach()

    def _connect_impl(self) -> None:
        if not hasattr(self, "_data_lock"):
            self._data_lock: threading.Lock = threading.Lock()

        self._subscriptions: dict[TupleKey, list[SubscriptionProtocol]] = {}

    def _disconnect_impl(self) -> None:
        with self._data_lock:
            self._subscriptions.clear()

    def _matches_pattern(
        self,
        topic: TupleKey,
        pattern: TupleKey,
        depth: int,
    ) -> bool:
        if len(topic) < len(pattern):
            return False

        if depth != -1 and len(topic) - len(pattern) != depth:
            return False

        return all(p == "*" or t == p for t, p in zip(topic, pattern, strict=False))

    def _notify_impl(self, topic: TupleKey) -> None:
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

    def _subscribe_impl(self, subscription: SubscriptionProtocol) -> None:
        topic_pattern = subscription.topic_pattern
        with self._data_lock:
            if topic_pattern not in self._subscriptions:
                self._subscriptions[topic_pattern] = []
            self._subscriptions[topic_pattern].append(subscription)

    def _unsubscribe_impl(self, subscription: SubscriptionProtocol) -> None:
        with self._data_lock:
            if subscription.topic_pattern in self._subscriptions:
                subs = self._subscriptions[subscription.topic_pattern]
                subs = [s for s in subs if s != subscription]
                if subs:
                    self._subscriptions[subscription.topic_pattern] = subs
                else:
                    del self._subscriptions[subscription.topic_pattern]


@attrs.define(frozen=True, slots=True, kw_only=True)
class InMemoryObserverSpec(ResourceSpec):
    """Specification for InMemoryObserver resource."""

    name: str = "in_memory_observer"
    factory: type = InMemoryObserver
    codec: Spec


if TYPE_CHECKING:
    _: type[ObserverProtocol[str]] = InMemoryObserver
