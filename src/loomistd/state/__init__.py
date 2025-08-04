"""
State implementation.
"""

from __future__ import annotations

import attrs

from loomi.tree import ObservableStorage, ObserverProtocol, StorageProtocol, Tree, Value
from loomicore.attach import Attach
from loomicore.resource import SyncResource
from loomicore.spec import ResourceSpec, Spec

__all__ = [
    "State",
    "StateSpec",
]


class State(SyncResource):
    """
    State implementation.
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
    factory: type = State
    storage: Spec
    observer: Spec
