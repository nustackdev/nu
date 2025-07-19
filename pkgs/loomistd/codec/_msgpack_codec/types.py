from __future__ import annotations

from typing import Protocol

from .._protocols import CodecProtocol

__all__ = [
    "MsgpackCodecKey",
    "MsgpackCodecValue",
    "MsgpackCodecEncodedKey",
    "MsgpackCodecEncodedValue",
    "MsgpackCodecProtocol",
]

MsgpackCodecKey = tuple[str, ...]
MsgpackCodecValue = (
    None
    | bytes
    | bool
    | int
    | float
    | str
    | list["MsgpackCodecValue"]
    | dict[str, "MsgpackCodecValue"]
)
MsgpackCodecEncodedKey = bytes
MsgpackCodecEncodedValue = bytes


class MsgpackCodecProtocol(
    CodecProtocol[
        MsgpackCodecKey, MsgpackCodecValue, MsgpackCodecEncodedKey, MsgpackCodecEncodedValue
    ],
    Protocol,
):
    """
    Msgpack codec protocol.
    """

    ...
