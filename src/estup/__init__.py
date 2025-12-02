"""estup (EveryShape Tuple) - codec for encoding/decoding tree storage keys.

This package provides codecs for converting tuple keys (containing strings and integers)
into formats suitable for key-value storage while preserving lexicographic ordering.

Available codecs:
- BinaryKeyCodec: Efficient binary encoding
- StringKeyCodec: Human-readable string encoding (extremely unnefficient, useful for debugging)

Key features:
- Lexicographic ordering preservation for KV storage compatibility
- Type safety with comprehensive error handling
- Support for mixed string/integer tuple keys
- Configurable constraints and validation

Example usage:
    >>> from everyshape.codec.key_codec import BinaryKeyCodec, StringKeyCodec
    >>>
    >>> # Binary codec for production use
    >>> binary_codec = BinaryKeyCodec()
    >>> key = ("users", 42, "profile", -10)
    >>> encoded = binary_codec.encode(key)
    >>> decoded = binary_codec.decode(encoded)
    >>> assert decoded == key
    >>>
    >>> # String codec for debugging/human readability
    >>> string_codec = StringKeyCodec()
    >>> key = ("users", 42, "profile")
    >>> encoded = string_codec.encode(key)  # Human-readable output
    >>> decoded = string_codec.decode(encoded)
    >>> assert decoded == key
"""

from __future__ import annotations

from .binary.binary_codec import BinaryKeyCodec
from .binary_py.binary_codec import PyBinaryKeyCodec
from .exceptions import (
    DecodeError,
    EncodeError,
    IntegerOverflowError,
    KeyCodecError,
    StringConstraintError,
)
from .protocols import KeyCodec
from .string.string_codec import StringKeyCodec
from .types import EncodedBinaryKey, EncodedStringKey, Key, KeyComponent


__all__ = [
    "BinaryKeyCodec",
    "DecodeError",
    "EncodeError",
    "EncodedBinaryKey",
    "EncodedStringKey",
    "IntegerOverflowError",
    "Key",
    "KeyCodec",
    "KeyCodecError",
    "KeyComponent",
    "PyBinaryKeyCodec",
    "StringConstraintError",
    "StringKeyCodec",
]
