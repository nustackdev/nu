"""
StateService implementation.
"""

from __future__ import annotations

from typing import Any

import attrs

from loomi import Attach, Spec, SyncService
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

    storage: StorageServiceProtocol[PathTuple, Value, Any, Any] = Attach()
    observer: ObserverServiceProtocol[PathTuple, Any] = Attach()

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


@attrs.define(frozen=True, slots=True, kw_only=True)
class StateSpec(Spec):
    name: str = "state"
    factory: type = StateService
    storage: Spec = attrs.field(factory=lambda: FileStorageSpec())
    observer: Spec = attrs.field(factory=lambda: InMemoryObserverSpec())
