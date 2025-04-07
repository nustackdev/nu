"""
State implementation combining storage and change notifications.

This module provides a complete state management solution with:
- Persistent storage
- Change notifications
- Transactional operations
- Type safety
"""

from __future__ import annotations

from typing import Any

from loomi.service import AsyncService, Attach
from loomistd.kv_storage import StorageProtocol
from loomistd.observer import ObserverProtocol, SubscriptionProtocol
from loomistd.tree_storage import TreeStorageBase, TreeStorageCore

from ._observable_kv import ObservableKVStorageCore
from ._types import StateCallbackFn, StateKey, StateValue

__all__ = [
    "State",
]


class State(AsyncService, TreeStorageBase[StateValue]):
    """
    State implementation that combines storage and change notifications.

    Features:
    - Persistent storage with configurable backend
    - Real-time change notifications
    - Transactional operations
    - Type-safe interfaces
    - Async-first design
    """

    _storage: StorageProtocol[StateKey, StateValue, Any, Any] = Attach(StorageProtocol)
    _observer: ObserverProtocol[StateKey, Any] = Attach(ObserverProtocol)

    async def setup(self):
        self._observable_kv_storage = ObservableKVStorageCore(
            storage=self._storage,
            observer=self._observer,
        )
        self._tree_storage_core = TreeStorageCore(self._observable_kv_storage)

    async def subscribe(
        self,
        key: StateKey,
        callback: StateCallbackFn,
        depth: int = 0,
    ) -> SubscriptionProtocol[StateKey]:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Async callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.


        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        return await self._observable_kv_storage.subscribe(key, callback, depth)

    async def unsubscribe(self, subscription: SubscriptionProtocol[StateKey]) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        await self._observable_kv_storage.unsubscribe(subscription)
