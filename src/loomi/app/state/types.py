from __future__ import annotations

from typing import Awaitable, Callable

__all__ = [
    "StatePath",
    "StatePathComponent",
    "StateValue",
    "AsyncStateCallbackFn",
    "SyncStateCallbackFn",
]


StatePathComponent = str
StatePath = tuple[StatePathComponent, ...]
StateValue = None | bytes | bool | int | float | str | list["StateValue"] | dict[str, "StateValue"]

AsyncStateCallbackFn = Callable[[StatePath], Awaitable[None]]
SyncStateCallbackFn = Callable[[StatePath], None]
