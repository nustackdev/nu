"""Type definitions for codec."""

from __future__ import annotations

from typing import TypeVar


__all__ = [
    "Key",
    "EncodedKeyT",
    "SupportedValuesT",
    "EncodedValueT",
]


Key = tuple[str | int, ...]
EncodedKeyT = TypeVar("EncodedKeyT", covariant=True)
SupportedValuesT = TypeVar("SupportedValuesT", contravariant=True)
EncodedValueT = TypeVar("EncodedValueT", covariant=True)
