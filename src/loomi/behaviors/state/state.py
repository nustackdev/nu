"""
StateService implementation.
"""

from __future__ import annotations

from typing import Any

import attrs

from loomi import Attach, ResourceSpec, Spec, SyncService
from loomistd.kv import StorageServiceProtocol
from loomistd.kv.file_storage import FileStorageSpec
from loomistd.observer import ObserverServiceProtocol
from loomistd.observer.in_memory import InMemoryObserverSpec

from .backend import ObservableStorage
from .tree import Tree
from .tree.types import PathTuple, Value

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
        self._tree = Tree(
            backend=ObservableStorage(
                storage=self.storage,
                observer=self.observer,
            )
        )

    @property
    def tree(self) -> Tree:
        """
        Get the state object.

        Returns:
            The state object
        """
        return self._tree


@attrs.define(frozen=True, slots=True, kw_only=True)
class StateSpec(ResourceSpec):
    name: str = "state"
    factory: type = StateService
    storage: Spec = attrs.field(factory=lambda: FileStorageSpec())
    observer: Spec = attrs.field(factory=lambda: InMemoryObserverSpec())
