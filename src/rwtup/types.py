"""Type definitions for key codec operations."""

from __future__ import annotations

from typing import TypeVar


# Core types for key components and keys
KeyComponent = str | int
Key = tuple[KeyComponent, ...]

# Generic type for encoded keys
EncodedKeyT = TypeVar("EncodedKeyT")

# Encoded key types for different codec implementations
EncodedBinaryKey = bytes
EncodedStringKey = str

__all__ = [
    "KeyComponent",
    "Key",
    "EncodedBinaryKey",
    "EncodedStringKey",
    "EncodedKeyT",
]
