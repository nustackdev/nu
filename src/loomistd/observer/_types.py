from __future__ import annotations

from typing import Any, TypeVar

from loomi.state import CallbackFn, Key

__all__ = [
    "Key",
    "ObserverKeyT",
    "ObserverEncodedKey",
    "ObserverEncodedKeyT",
    "ObserverCallbackFn",
]

ObserverKeyT = TypeVar("ObserverKeyT", bound=Key)
ObserverEncodedKey = Any
ObserverEncodedKeyT = TypeVar("ObserverEncodedKeyT", bound=ObserverEncodedKey)
ObserverCallbackFn = CallbackFn
