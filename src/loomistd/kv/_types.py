from __future__ import annotations

from typing import Literal, TypeVar

from loomi.tree import Key, Value, ValueT

__all__ = [
    "Key",
    "Value",
    "ValueT",
    "StorageKeyT",
    "StorageEncodedKeyT",
    "StorageEncodedValueT",
    "StorageMode",
]

StorageKeyT = TypeVar("StorageKeyT", bound=Key)
StorageEncodedKeyT = TypeVar("StorageEncodedKeyT")
StorageEncodedValueT = TypeVar("StorageEncodedValueT")
StorageMode = Literal["read", "write"]
