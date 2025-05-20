"""
StateService implementation.
"""

from __future__ import annotations

from typing import Any

from loomi import Spec, SpecField, SyncService, UseService
from loomistd.kv import StorageServiceProtocol
from loomistd.observer import ObserverServiceProtocol
from loomistd.specs import InMemoryObserverSpec, SyncFileStorageSpec

from .._types import StatePath, StateValue
from .backend import ObservableKVBackend
from .state import State

__all__ = [
    "State",
    "StateSpec",
]


class StateService(SyncService):
    """
    StateService implementation.
    """

    _backend: ObservableKVBackend
    _state: State

    storage: StorageServiceProtocol[StatePath, StateValue, Any, Any] = UseService()
    observer: ObserverServiceProtocol[StatePath, Any] = UseService()

    def setup(self):
        self._backend = ObservableKVBackend(
            storage=self.storage,
            observer=self.observer,
        )
        self._state = State(self._backend)

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
        return self._state


class StateSpec(Spec):
    name: str = SpecField(default="state")
    factory: type = SpecField(default=StateService)
    storage: Spec = SpecField(default_factory=SyncFileStorageSpec)
    observer: Spec = SpecField(default_factory=InMemoryObserverSpec)
