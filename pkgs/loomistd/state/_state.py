"""
State implementation combining storage and change notifications.

This module provides a complete state management solution with:
- Persistent storage
- Change notifications
- Transactional operations
- Type safety
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loomi.attr import UseService
from loomi.interfaces.state.observer import AsyncSubscriptionProtocol
from loomi.interfaces.state.state import AsyncStateProtocol
from loomi.service import AsyncService
from loomi.spec import Spec, SpecField
from loomistd.kv_storage import StorageServiceProtocol
from loomistd.kv_storage.file_storage import FileStorageSpec
from loomistd.observer import ObserverServiceProtocol
from loomistd.observer.in_memory import InMemoryObserverSpec
from loomistd.tree_storage import TreeStorageBase, TreeStorageCore

from ._observable_kv import ObservableKVStorageCore
from ._types import StateCallbackFn, StateKey, StateValue

__all__ = [
    "State",
    "StateSpec",
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

    storage_srv: StorageServiceProtocol[StateKey, StateValue, Any, Any] = UseService()
    observer_srv: ObserverServiceProtocol[StateKey, Any] = UseService()

    async def setup(self):
        self._observable_kv_storage = ObservableKVStorageCore(
            storage=self.storage_srv,
            observer=self.observer_srv,
        )
        self._tree_storage_core = TreeStorageCore(self._observable_kv_storage)

    async def subscribe(
        self,
        key: StateKey,
        callback: StateCallbackFn,
        depth: int = 0,
    ) -> AsyncSubscriptionProtocol:
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

    async def unsubscribe(self, subscription: AsyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        await self._observable_kv_storage.unsubscribe(subscription)


class StateSpec(Spec):
    name: str = SpecField(default="state")
    factory: type = SpecField(default=State)
    storage_srv: Spec = SpecField(default=FileStorageSpec())
    observer_srv: Spec = SpecField(default=InMemoryObserverSpec())


if TYPE_CHECKING:
    _: type[AsyncStateProtocol] = State
