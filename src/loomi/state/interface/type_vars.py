from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .state import AsyncStateServiceProtocol, SyncStateServiceProtocol
    from .tree import AsyncStateProtocol, SyncStateProtocol
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
    "StateServiceT",
    "StateServiceT_co",
    "StateServiceT_contra",
    "SyncStateServiceT",
    "SyncStateServiceT_co",
    "SyncStateServiceT_contra",
]

# --- Values --- #

StorageValueT = TypeVar("StorageValueT", bound="Value")
TreeValueT = TypeVar("TreeValueT", bound="Value")
StateValueT = TypeVar("StateValueT", bound="Value")


# --- State Service --- #

StateServiceT = TypeVar(
    "StateServiceT",
    bound="AsyncStateServiceProtocol | SyncStateServiceProtocol",
)
StateServiceT_co = TypeVar(
    "StateServiceT_co",
    bound="AsyncStateServiceProtocol | SyncStateServiceProtocol",
    covariant=True,
)
StateServiceT_contra = TypeVar(
    "StateServiceT_contra",
    bound="AsyncStateServiceProtocol | SyncStateServiceProtocol",
    contravariant=True,
)
SyncStateServiceT = TypeVar(
    "SyncStateServiceT",
    bound="SyncStateServiceProtocol",
)
SyncStateServiceT_co = TypeVar(
    "SyncStateServiceT_co",
    bound="SyncStateServiceProtocol",
    covariant=True,
)
SyncStateServiceT_contra = TypeVar(
    "SyncStateServiceT_contra",
    bound="SyncStateServiceProtocol",
    contravariant=True,
)


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
