from __future__ import annotations

from typing import Any, TypeVar

from loomi.state.interface.types import ObserverKey, SyncCallbackFn

__all__ = [
    "ObserverKey",
    "ObserverKeyT",
    "ObserverEncodedKey",
    "ObserverEncodedKeyT",
    "ObserverCallbackFn",
]

ObserverKeyT = TypeVar("ObserverKeyT", bound=ObserverKey)
ObserverEncodedKey = Any
ObserverEncodedKeyT = TypeVar("ObserverEncodedKeyT", bound=ObserverEncodedKey)
ObserverCallbackFn = SyncCallbackFn
