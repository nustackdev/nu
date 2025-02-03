# Type markers as integers for faster comparison
from dataclasses import dataclass
from typing import Protocol, TypeAlias, runtime_checkable

from .._protocols import CodecProtocol

BinaryCodecKey: TypeAlias = tuple[str, ...]
BinaryCodecValue: TypeAlias = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["BinaryCodecValue"]
    | dict[str, "BinaryCodecValue"]
)
BinaryCodecEncodedKey: TypeAlias = bytes
BinaryCodecEncodedValue: TypeAlias = bytes


@dataclass
class DecoderState:
    """Track decoder state to avoid deep recursion."""

    data: bytes
    offset: int = 0
    depth: int = 0


@runtime_checkable
class BinaryCodecProtocol(
    CodecProtocol[BinaryCodecKey, BinaryCodecValue, BinaryCodecEncodedKey, BinaryCodecEncodedValue],
    Protocol,
):
    """
    Binary codec protocol.
    """

    ...
