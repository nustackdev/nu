from __future__ import annotations

from typing import Protocol

from .._protocols import CodecProtocol


__all__ = [
    "JSONCodecKey",
    "JSONCodecValue",
    "JSONCodecEncodedKey",
    "JSONCodecEncodedValue",
    "JSONCodecProtocol",
]

JSONCodecKey = tuple[str, ...]
JSONCodecValue = (
    None | bytes | bool | int | float | str | list["JSONCodecValue"] | dict[str, "JSONCodecValue"]
)
JSONCodecEncodedKey = str
JSONCodecEncodedValue = str


class JSONCodecProtocol(
    CodecProtocol[JSONCodecKey, JSONCodecValue, JSONCodecEncodedKey, JSONCodecEncodedValue],
    Protocol,
):
    """
    JSON codec protocol.
    """

    ...
