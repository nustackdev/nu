from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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
BinaryCodecValue = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["BinaryCodecValue"]
    | dict[str, "BinaryCodecValue"]
)
BinaryCodecEncodedKey = bytes
BinaryCodecEncodedValue = bytes


@dataclass
class DecoderState:
    """Track decoder state to avoid deep recursion."""

    data: bytes
    offset: int = 0
    depth: int = 0


class BinaryCodecProtocol(
    CodecProtocol[BinaryCodecKey, BinaryCodecValue, BinaryCodecEncodedKey, BinaryCodecEncodedValue],
    Protocol,
):
    """
    Binary codec protocol.
    """

    ...
