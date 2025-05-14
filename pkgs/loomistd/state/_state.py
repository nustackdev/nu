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
from loomi.interfaces.state.observer import SyncSubscriptionProtocol
from loomi.interfaces.state.state import SyncStateProtocol
from loomi.service import SyncService
from loomi.spec import Spec, SpecField
from loomistd.kv import StorageServiceProtocol
from loomistd.kv.file_storage import FileStorageSpec
from loomistd.observer import ObserverServiceProtocol
from loomistd.observer.in_memory import InMemoryObserverSpec
from loomistd.tree import TreeStorageBase, TreeStorageCore

from ._observable_kv import ObservableKVStorageCore
from ._types import StateCallbackFn, StateKey, StateValue

__all__ = [
    "State",
    "StateSpec",
]


class State(SyncService, TreeStorageBase[StateValue]):
    """
    State implementation that combines storage and change notifications.

    Features:
    - Persistent storage with configurable backend
    - Real-time change notifications
    - Transactional operations
    - Type-safe interfaces
    """

    storage_srv: StorageServiceProtocol[StateKey, StateValue, Any, Any] = UseService()
    observer_srv: ObserverServiceProtocol[StateKey, Any] = UseService()

    @property
    def is_sync(self) -> bool:
        """
        Check if the state is synchronous.

        Returns:
            True if the state is synchronous, False otherwise
        """
        return True

    def setup(self):
        self._observable_kv_storage = ObservableKVStorageCore(
            storage=self.storage_srv,
            observer=self.observer_srv,
        )
        self._tree_storage_core = TreeStorageCore(self._observable_kv_storage)

    def subscribe(
        self,
        key: StateKey,
        callback: StateCallbackFn,
        depth: int = 0,
    ) -> SyncSubscriptionProtocol:
        """
        Subscribe to changes under key prefix.

        Args:
            key: Key prefix to subscribe to
            callback: Sync callback function for notifications
            depth: Depth of topic pattern matching (default: 0 for exact match)
                If set to 0, matches exact topic; if set to 1, matches prefix; if set to -1, matches all subtopics.

        Returns:
            Subscription object for unsubscribing

        Raises:
            ObserverError: If subscription fails
        """
        return self._observable_kv_storage.subscribe(key, callback, depth)

    def unsubscribe(self, subscription: SyncSubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        self._observable_kv_storage.unsubscribe(subscription)


class StateSpec(Spec):
    name: str = SpecField(default="state")
    factory: type = SpecField(default=State)
    storage_srv: Spec = SpecField(default_factory=FileStorageSpec)
    observer_srv: Spec = SpecField(default_factory=InMemoryObserverSpec)


if TYPE_CHECKING:
    _: type[SyncStateProtocol] = State
