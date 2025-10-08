"""
Codec package for Redwood storage.

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

from .codec import StorageCodec, StorageCodecSpec
from .protocols import (
    KeyCodecProtocol,
    StorageCodecProtocol,
    ValueCodecProtocol,
)
from .types import (
    EncodedKeyT,
    EncodedValueT,
    Key,
    SupportedValuesT,
)


__all__ = [
    # Core codec
    "StorageCodec",
    "StorageCodecSpec",
    # Protocols
    "KeyCodecProtocol",
    "ValueCodecProtocol",
    "StorageCodecProtocol",
    # Type variables
    "Key",
    "EncodedKeyT",
    "SupportedValuesT",
    "EncodedValueT",
    # Aliases
    "BinaryCodec",
    "BinaryCodecSpec",
    "TextCodec",
    "TextCodecSpec",
]

########################################################
# Aliases for common codec types
#########################################################

from rwtup import BinaryKeyCodec, StringKeyCodec

from .adapters.json import JSONCodec
from .adapters.micropack import MicroPackCodec
from .adapters.types import (
    JSONEncoded,
    JSONSupportedValues,
    MicroPackEncoded,
    MicroPackSupportedValues,
)


# MicroPack-based binary codec
BinaryCodec = StorageCodec[bytes, MicroPackSupportedValues, MicroPackEncoded]
BinaryCodecSpec = partial(
    StorageCodecSpec,
    key_codec=BinaryKeyCodec,
    value_codec=MicroPackCodec,
)

# JSON-based text codec
TextCodec = StorageCodec[str, JSONSupportedValues, JSONEncoded]
TextCodecSpec = partial(
    StorageCodecSpec,
    key_codec=StringKeyCodec,
    value_codec=JSONCodec,
)
