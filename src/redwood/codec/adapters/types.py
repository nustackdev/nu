"""Type definitions for codec adapters."""

from __future__ import annotations

from typing import Any


__all__ = [
    "PassthroughEncoded",
    "MessagePackEncoded",
    "MicroPackEncoded",
    "JSONEncoded",
    "PickleEncoded",
]


# Passthrough codec types - no transformation
PassthroughEncoded = Any


# MessagePack codec types - binary serialization
MessagePackEncoded = bytes


# MicroPack codec types - optimized binary serialization
MicroPackEncoded = bytes


# JSON codec types - text serialization with base64 for bytes
JSONEncoded = str


# Pickle codec types - Python object serialization
PickleEncoded = bytes
