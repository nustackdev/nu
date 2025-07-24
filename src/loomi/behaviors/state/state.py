"""
StateService implementation.
"""

from __future__ import annotations

import attrs

from loomicore.attach import Attach
from loomicore.resource import SyncResource
from loomicore.spec import ResourceSpec, Spec

from .backend import ObservableStorage, ObserverProtocol, StorageProtocol
from .tree import Tree
from .tree.types import Value

__all__ = [
    "StateService",
    "StateSpec",
]


class StateService(SyncResource):
    """
    StateService implementation.
    """

    storage: StorageProtocol[Value] = Attach()
    observer: ObserverProtocol = Attach()

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
    storage: Spec
    observer: Spec
