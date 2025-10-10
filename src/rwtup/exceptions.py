"""Exception classes for key codec operations."""

from __future__ import annotations


class KeyCodecError(Exception):
    """Base exception for all key codec errors."""

    pass


class EncodeError(KeyCodecError):
    """Raised when encoding a key fails.

    This can occur due to:
    - Invalid key structure (empty tuple, wrong types)
    - Value constraints violations (integer overflow, string too long)
    - Encoding-specific limitations
    """

    pass


class DecodeError(KeyCodecError):
    """Raised when decoding an encoded key fails.

    This can occur due to:
    - Corrupted or invalid encoded data
    - Unsupported format versions
    - Truncated data
    """

    pass


class IntegerOverflowError(EncodeError):
    """Raised when an integer value exceeds the codec's supported range.

    Different codecs may have different integer limits:
    - Binary codec: int64 range (-2^63 to 2^63-1)
    - String codec: uint16 range (0 to 65535) for human readability
    """

    def __init__(self, value: int, min_value: int, max_value: int) -> None:
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(f"Integer {value} out of supported range [{min_value}, {max_value}]")


class StringConstraintError(EncodeError):
    """Raised when a string violates codec-specific constraints.

    This can occur due to:
    - Empty strings (not allowed in keys)
    - Strings exceeding maximum length
    - Invalid characters for specific codecs
    """

    pass


__all__ = [
    "KeyCodecError",
    "EncodeError",
    "DecodeError",
    "IntegerOverflowError",
    "StringConstraintError",
]
