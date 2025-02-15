from typing import Protocol

from _typeshed import Incomplete

from .._protocols import CodecProtocol

__all__ = [
    "JSONCodecKey",
    "JSONCodecValue",
    "JSONCodecEncodedKey",
    "JSONCodecEncodedValue",
    "JSONCodecProtocol",
]

JSONCodecKey = tuple[str, ...]
JSONCodecValue: Incomplete
JSONCodecEncodedKey = str
JSONCodecEncodedValue = str

class JSONCodecProtocol(
    CodecProtocol[JSONCodecKey, JSONCodecValue, JSONCodecEncodedKey, JSONCodecEncodedValue],
    Protocol,
): ...
