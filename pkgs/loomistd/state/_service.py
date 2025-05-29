"""
StateService implementation.
"""

from __future__ import annotations

from typing import Any

from loomi import Spec, SpecField, SyncService, UseService
from loomistd.kv import StorageServiceProtocol
from loomistd.observer import ObserverServiceProtocol
from loomistd.specs import InMemoryObserverSpec, SyncFileStorageSpec
from loomistd.tree.backend.observable_kv import ObservableKVBackend
from loomistd.tree.types import PathTuple, Value

from ._state import State

__all__ = [
    "StateService",
    "StateSpec",
]


class StateService(SyncService):
    """
    StateService implementation.
    """

    storage: StorageServiceProtocol[PathTuple, Value, Any, Any] = UseService()
    observer: ObserverServiceProtocol[PathTuple, Any] = UseService()

    _adapter: State

    def setup(self):
        self._adapter = State(
            backend=ObservableKVBackend(
                storage=self.storage,
                observer=self.observer,
            )
        )

    @property
    def is_sync(self) -> bool:
        """
        Check if the state is synchronous.

        Returns:
            True if the state is synchronous, False otherwise
        """
        return True

    @property
    def state(self) -> State:
        """
        Get the state object.

        Returns:
            The state object
        """
        return self._adapter


class StateSpec(Spec):
    name: str = SpecField(default="state")
    factory: type = SpecField(default=StateService)
    storage: Spec = SpecField(default_factory=SyncFileStorageSpec)
    observer: Spec = SpecField(default_factory=InMemoryObserverSpec)
