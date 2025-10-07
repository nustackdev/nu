from __future__ import annotations

from typing import Any, Protocol

from .._protocols import CodecProtocol


__all__ = [
    "PassthroughCodecKey",
    "PassthroughCodecValue",
    "PassthroughCodecEncodedKey",
    "PassthroughCodecEncodedValue",
    "PassthroughCodecProtocol",
]

PassthroughCodecKey = tuple[str, ...]
PassthroughCodecValue = Any
PassthroughCodecEncodedKey = str
PassthroughCodecEncodedValue = Any


class PassthroughCodecProtocol(
    CodecProtocol[
        PassthroughCodecKey,
        PassthroughCodecValue,
        PassthroughCodecEncodedKey,
        PassthroughCodecEncodedValue,
    ],
    Protocol,
):
    """
    Passthrough codec protocol.
    """

    ...
