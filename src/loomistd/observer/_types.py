from __future__ import annotations

from typing import Any, TypeVar

from loomi.behaviors.state.protocols.types import ObserverKey

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
