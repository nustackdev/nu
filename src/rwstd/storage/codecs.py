"""Codec package for Redwood storage.

This package provides a modular codec system for encoding/decoding keys and
values in storage engines. It includes:

- Protocol definitions for key, value, and storage codecs
- Concrete adapter implementations for various serialization formats
- Unified StorageCodec that combines key and value codecs

Architecture:
    - adapters/: Concrete codec implementations (JSON, MessagePack, Pickle, etc.)
    - protocols.py: Protocol definitions for type safety
    - codec.py: StorageCodec implementation combining key and value codecs

Usage:
    >>> from redwood.codec import StorageCodec, StorageCodecSpec
    >>> from redwood.codec.adapters import MsgpackCodec, JSONCodec
    >>>
    >>> spec = StorageCodecSpec(
    ...     key_codec=MsgpackCodec,
    ...     value_codec=JSONCodec,
    ... )
    >>> codec = StorageCodec(spec=spec)
    >>> codec.setup()
    >>>
    >>> # Encode/decode keys and values
    >>> encoded_key = codec.encode_key((1, 2, 3))
    >>> decoded_key = codec.decode_key(encoded_key)
    >>> encoded_value = codec.encode_value({"data": "example"})
    >>> decoded_value = codec.decode_value(encoded_value)
"""

from __future__ import annotations

from functools import partial

from redwood.storage import Codec


__all__ = [
    "BinaryCodec",
    "NoOpCodec",
    "TextCodec",
]

# =========================================================
# Aliases for common codec types
# =========================================================

from rwtup import BinaryKeyCodec, StringKeyCodec

from .codec_json import JSONCodec
from .codec_micropack import MicroPackCodec
from .codec_passthrough import PassthroughCodec


# MicroPack-based binary codec
BinaryCodec = partial(
    Codec,
    key_codec_cls=BinaryKeyCodec,
    value_codec_cls=MicroPackCodec,
)

# JSON-based text codec
TextCodec = partial(
    Codec,
    key_codec_cls=StringKeyCodec,
    value_codec_cls=JSONCodec,
)

# No-op codec
NoOpCodec = partial(
    Codec,
    key_codec_cls=StringKeyCodec,
    value_codec_cls=PassthroughCodec,
)
