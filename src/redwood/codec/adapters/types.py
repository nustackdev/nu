"""Type definitions for codec adapters."""

from __future__ import annotations

from typing import Any


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
MessagePackSupportedValues = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["MessagePackSupportedValues"]
    | dict[str, "MessagePackSupportedValues"]
)
MessagePackEncoded = bytes


# MicroPack codec types - optimized binary serialization
MicroPackSupportedValues = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["MicroPackSupportedValues"]
    | dict[str, "MicroPackSupportedValues"]
)
MicroPackEncoded = bytes


# JSON codec types - text serialization with base64 for bytes
JSONSupportedValues = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["JSONSupportedValues"]
    | dict[str, "JSONSupportedValues"]
)
JSONEncoded = str


# Pickle codec types - Python object serialization
PickleSupportedValues = Any
PickleEncoded = bytes
