from __future__ import annotations

from typing import Any, Awaitable, Callable

__all__ = [
    "StateKey",
    "StateValue",
    "AsyncStateCallbackFn",
    "SyncStateCallbackFn",
]

StateKey = tuple[str, ...]
StateValue = Any
AsyncStateCallbackFn = Callable[[StateKey], Awaitable[None]]
SyncStateCallbackFn = Callable[[StateKey], None]
