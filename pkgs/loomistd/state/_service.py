"""
StateService implementation.
"""

from __future__ import annotations

from typing import Any

from loomi import Spec, SpecField, SyncService, UseService
from loomistd.kv import StorageServiceProtocol
from loomistd.kv.file_storage import FileStorageSpec
from loomistd.observer import ObserverServiceProtocol
from loomistd.observer.in_memory import InMemoryObserverSpec
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

    def setup(self):
        self._state = State(
            backend=ObservableKVBackend(
                storage=self.storage,
                observer=self.observer,
            )
        )

    @property
    def state(self) -> State:
        """
        Get the state object.

        Returns:
            The state object
        """
        return self._state


class StateSpec(Spec):
    name: str = SpecField(default="state")
    factory: type = SpecField(default=StateService)
    storage: Spec = SpecField(default_factory=FileStorageSpec)
    observer: Spec = SpecField(default_factory=InMemoryObserverSpec)
