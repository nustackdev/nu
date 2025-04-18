from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeAlias

if TYPE_CHECKING:
    from .type_vars import StateValueT, StorageValueT, TreeValueT

__all__ = [
    "KeyBase",
    "Key",
    "Value",
    "StorageKey",
    "StorageValue",
    "StorageValueT",
    "ObserverKey",
    "TreePathComponent",
    "TreePath",
    "TreeValue",
    "TreeValueT",
    "TreeValueContainer",
    "StatePathComponent",
    "StatePath",
    "StateValue",
    "StateValueT",
    "StateValueContainer",
    "AsyncCallbackFn",
    "SyncCallbackFn",
]

# Base types
KeyBase = str
Key = tuple[KeyBase, ...]
Value = Any

# KV storage types
StorageKey = Key
StorageValue = Value

# Observability types
ObserverKey = Key

# Tree storage types
TreePathComponent = KeyBase
TreePath = Key
TreeValue = Value
TreeValueContainer: TypeAlias = (
    "TreeValueT | list[TreeValueT] | dict[TreePathComponent, TreeValueT]"
)

# State types
StatePathComponent = KeyBase
StatePath = Key
StateValue = Value
StateValueContainer: TypeAlias = (
    "StateValueT | list[StateValueT] | dict[StatePathComponent, StateValueT]"
)

# Callbacks
AsyncCallbackFn = Callable[[Key], Awaitable[None]]
SyncCallbackFn = Callable[[Key], None]
