"""
StateService implementation.
"""

from __future__ import annotations

from typing import Any

from loomi import Spec, SpecField, SyncService, UseService
from loomistd.kv import StorageServiceProtocol
from loomistd.observer import ObserverServiceProtocol
from loomistd.specs import InMemoryObserverSpec, SyncFileStorageSpec

from .backend.observable_kv import ObservableKVBackend
from .tree import Tree
from .types import PathTuple, Value

__all__ = [
    "State",
    "StateSpec",
]


class State(Tree):
    """
    Example state class that extends the Tree class.
    This is a placeholder for the actual implementation.
    """

    pass


class StateService(SyncService):
    """
    StateService implementation.
    """

    _tree: State

    storage: StorageServiceProtocol[PathTuple, Value, Any, Any] = UseService()
    observer: ObserverServiceProtocol[PathTuple, Any] = UseService()

    def setup(self):
        self._tree = State(
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
        return self._tree


class StateSpec(Spec):
    name: str = SpecField(default="state")
    factory: type = SpecField(default=StateService)
    storage: Spec = SpecField(default_factory=SyncFileStorageSpec)
    observer: Spec = SpecField(default_factory=InMemoryObserverSpec)
