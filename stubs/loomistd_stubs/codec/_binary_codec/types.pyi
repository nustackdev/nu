from dataclasses import dataclass
from typing import Protocol

from _typeshed import Incomplete

from .._protocols import CodecProtocol

__all__ = [
    "BinaryCodecKey",
    "BinaryCodecValue",
    "BinaryCodecEncodedKey",
    "BinaryCodecEncodedValue",
    "DecoderState",
    "BinaryCodecProtocol",
]

BinaryCodecKey = tuple[str, ...]
BinaryCodecValue: Incomplete
BinaryCodecEncodedKey = bytes
BinaryCodecEncodedValue = bytes

@dataclass
class DecoderState:
    data: bytes
    offset: int = ...
    depth: int = ...

class BinaryCodecProtocol(
    CodecProtocol[BinaryCodecKey, BinaryCodecValue, BinaryCodecEncodedKey, BinaryCodecEncodedValue],
    Protocol,
): ...
