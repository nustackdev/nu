"""Type definitions for codec adapters."""

from __future__ import annotations

from typing import Any


__all__ = [
    "JSONEncoded",
    "MessagePackEncoded",
    "MicroPackEncoded",
    "PassthroughEncoded",
    "PickleEncoded",
]


PassthroughEncoded = Any  # Passthrough codec types - no transformation
MessagePackEncoded = bytes  # MessagePack codec types - binary serialization
MicroPackEncoded = bytes  # MicroPack codec types - optimized binary serialization
JSONEncoded = str  # JSON codec types - text serialization with base64 for bytes
PickleEncoded = bytes  # Pickle codec types - Python object serialization
