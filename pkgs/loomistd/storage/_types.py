from __future__ import annotations

from typing import Literal, TypeVar

__all__ = [
    "StorageKeyT",
    "StorageValueT",
    "StorageEncodedKeyT",
    "StorageEncodedValueT",
    "StorageMode",
]

StorageKeyT = TypeVar("StorageKeyT")
StorageValueT = TypeVar("StorageValueT")
StorageEncodedKeyT = TypeVar("StorageEncodedKeyT")
StorageEncodedValueT = TypeVar("StorageEncodedValueT")
StorageMode = Literal["read", "write"]
