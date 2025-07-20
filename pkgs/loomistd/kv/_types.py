from __future__ import annotations

from typing import Literal, TypeVar

from loomi.behaviors.state.protocols.type_vars import StorageValueT
from loomi.behaviors.state.protocols.types import StorageKey, StorageValue

__all__ = [
    "StorageKey",
    "StorageKeyT",
    "StorageValue",
    "StorageValueT",
    "StorageEncodedKeyT",
    "StorageEncodedValueT",
    "StorageMode",
]

StorageKeyT = TypeVar("StorageKeyT", bound=StorageKey)
StorageEncodedKeyT = TypeVar("StorageEncodedKeyT")
StorageEncodedValueT = TypeVar("StorageEncodedValueT")
StorageMode = Literal["read", "write"]
