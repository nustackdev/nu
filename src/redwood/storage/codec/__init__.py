"""Codec protocols for encoding and decoding keys and values."""

from __future__ import annotations

from .codec import Codec
from .protocol import CodecProtocol, KeyCodecProtocol, ValueCodecProtocol


__all__ = [
    "Codec",
    "CodecProtocol",
    "KeyCodecProtocol",
    "ValueCodecProtocol",
]
