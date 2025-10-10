"""Type definitions for codec."""

from __future__ import annotations

from typing import TypeVar

from redwood.types import StorageKey, StorageKeyComponent


__all__ = [
    "Key",
    "EncodedKeyT",
    "SupportedValuesT",
    "EncodedValueT",
]

KeyComponent = StorageKeyComponent
Key = StorageKey
EncodedKeyT = TypeVar("EncodedKeyT")
SupportedValuesT = TypeVar("SupportedValuesT")
EncodedValueT = TypeVar("EncodedValueT")
