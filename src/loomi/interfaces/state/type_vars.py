from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .state import AsyncStateProtocol, SyncStateProtocol
    from .tree import AsyncTreeDictProtocol, SyncTreeDictProtocol
    from .types import Value

__all__ = [
    "StorageValueT",
    "TreeValueT",
    "StateValueT",
    "StateT",
    "StateT_co",
    "StateT_contra",
    "SyncStateT",
    "SyncStateT_co",
    "SyncStateT_contra",
    "StateDictT",
    "StateDictT_co",
    "StateDictT_contra",
    "SyncStateDictT",
    "SyncStateDictT_co",
    "SyncStateDictT_contra",
]

# --- Values --- #

StorageValueT = TypeVar("StorageValueT", bound="Value")
TreeValueT = TypeVar("TreeValueT", bound="Value")
StateValueT = TypeVar("StateValueT", bound="Value")


# --- State --- #

StateT = TypeVar(
    "StateT",
    bound="AsyncStateProtocol | SyncStateProtocol",
)
StateT_co = TypeVar(
    "StateT_co",
    bound="AsyncStateProtocol | SyncStateProtocol",
    covariant=True,
)
StateT_contra = TypeVar(
    "StateT_contra",
    bound="AsyncStateProtocol | SyncStateProtocol",
    contravariant=True,
)
SyncStateT = TypeVar(
    "SyncStateT",
    bound="SyncStateProtocol",
)
SyncStateT_co = TypeVar(
    "SyncStateT_co",
    bound="SyncStateProtocol",
    covariant=True,
)
SyncStateT_contra = TypeVar(
    "SyncStateT_contra",
    bound="SyncStateProtocol",
    contravariant=True,
)


# --- Higher-level state interfaces --- #

StateDictT = TypeVar(
    "StateDictT",
    bound="AsyncTreeDictProtocol | SyncTreeDictProtocol",
)
StateDictT_co = TypeVar(
    "StateDictT_co",
    bound="AsyncTreeDictProtocol | SyncTreeDictProtocol",
    covariant=True,
)
StateDictT_contra = TypeVar(
    "StateDictT_contra",
    bound="AsyncTreeDictProtocol | SyncTreeDictProtocol",
    contravariant=True,
)
SyncStateDictT = TypeVar(
    "SyncStateDictT",
    bound="SyncTreeDictProtocol",
)
SyncStateDictT_co = TypeVar(
    "SyncStateDictT_co",
    bound="SyncTreeDictProtocol",
    covariant=True,
)
SyncStateDictT_contra = TypeVar(
    "SyncStateDictT_contra",
    bound="SyncTreeDictProtocol",
    contravariant=True,
)
