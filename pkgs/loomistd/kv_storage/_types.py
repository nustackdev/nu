from __future__ import annotations

from typing import Any, Literal, TypeVar

__all__ = [
    "StorageKeyT",
    "StorageValueT",
    "StorageEncodedKeyT",
    "StorageEncodedValueT",
    "StorageMode",
]

StorageKeyT = TypeVar("StorageKeyT", bound=tuple[str, ...])
StorageValue = Any
StorageValueT = TypeVar("StorageValueT", bound=StorageValue)
StorageEncodedKeyT = TypeVar("StorageEncodedKeyT")
StorageEncodedValueT = TypeVar("StorageEncodedValueT")
StorageMode = Literal["read", "write"]
