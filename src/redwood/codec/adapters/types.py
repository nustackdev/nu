"""Type definitions for codec adapters."""

from __future__ import annotations

from typing import Any

from redwood.types import CompositeValue


__all__ = [
    "PassthroughSupportedValues",
    "PassthroughEncoded",
    "MessagePackSupportedValues",
    "MessagePackEncoded",
    "MicroPackSupportedValues",
    "MicroPackEncoded",
    "JSONSupportedValues",
    "JSONEncoded",
    "PickleSupportedValues",
    "PickleEncoded",
]


# Passthrough codec types - no transformation
PassthroughSupportedValues = Any
PassthroughEncoded = Any


# MessagePack codec types - binary serialization
MessagePackSupportedValues = CompositeValue
MessagePackEncoded = bytes


# MicroPack codec types - optimized binary serialization
MicroPackSupportedValues = CompositeValue
MicroPackEncoded = bytes


# JSON codec types - text serialization with base64 for bytes
JSONSupportedValues = CompositeValue
JSONEncoded = str


# Pickle codec types - Python object serialization
PickleSupportedValues = Any
PickleEncoded = bytes
