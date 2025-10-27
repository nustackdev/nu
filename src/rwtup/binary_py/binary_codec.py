"""Binary key codec implementation for lexicographic ordering preservation."""

from __future__ import annotations

import re
from typing import Final

from ..exceptions import DecodeError, EncodeError, IntegerOverflowError, StringConstraintError
from ..protocols import KeyCodec
from ..types import EncodedBinaryKey, Key, KeyComponent


# Type markers for lexicographic ordering (int < str)
_TYPE_INT: Final[bytes] = b"\x01"
_TYPE_STR: Final[bytes] = b"\x02"

# Component separator - using invalid UTF-8 byte, no escaping needed
_SEPARATOR: Final[bytes] = b"\xff"

# Integer range constraints
_INT64_MIN: Final[int] = -(2**63)
_INT64_MAX: Final[int] = 2**63 - 1
_INT64_BIAS: Final[int] = 2**63  # Bias for offset binary encoding


# Constants for validation
MAX_STRING_LENGTH: Final[int] = 10 * 1024 * 1024  # 10MB
MIN_STRING_LENGTH: Final[int] = 1  # No empty strings allowed

# Pattern for valid string components (printable ASCII + common Unicode)
# This ensures human readability and avoids problematic characters
VALID_STRING_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[\w\s\-_./:@#$%&+=<>?!()[\]{}|~`^*]+$", re.UNICODE
)


def validate_key(key: Key) -> None:
    """Validate that a key tuple meets basic requirements.

    Args:
        key: Tuple to validate

    Raises:
        EncodeError: If key structure is invalid
        StringConstraintError: If string components violate constraints
    """
    from ..exceptions import EncodeError

    if not isinstance(key, tuple):
        raise EncodeError(f"Key must be a tuple, got {type(key).__name__}")

    if not key:
        raise EncodeError("Empty tuple not allowed as key")

    for i, component in enumerate(key):
        validate_key_component(component, i)


def validate_key_component(component: KeyComponent, index: int) -> None:
    """Validate a single key component.

    Args:
        component: Component to validate
        index: Position in the key tuple (for error messages)

    Raises:
        EncodeError: If component type is invalid
        StringConstraintError: If string component violates constraints
    """
    from ..exceptions import EncodeError

    if isinstance(component, str):
        validate_string_component(component, index)
    elif isinstance(component, int):
        # Integer validation is codec-specific, done in individual codecs
        pass
    else:
        raise EncodeError(
            f"Component at index {index} must be str or int, got {type(component).__name__}"
        )


def validate_string_component(value: str, index: int) -> None:
    """Validate a string component meets general constraints.

    Args:
        value: String to validate
        index: Position in the key tuple (for error messages)

    Raises:
        StringConstraintError: If string violates constraints
    """
    if len(value) < MIN_STRING_LENGTH:
        raise StringConstraintError(f"Empty string at index {index} not allowed")

    if len(value) > MAX_STRING_LENGTH:
        raise StringConstraintError(
            f"String at index {index} too long: {len(value)} chars (max {MAX_STRING_LENGTH})"
        )

    # Check for valid characters (human-readable constraint)
    if not VALID_STRING_PATTERN.match(value):
        raise StringConstraintError(
            f"String at index {index} contains invalid characters. "
            f"Only printable ASCII and common Unicode characters are allowed."
        )


def _encode_integer(value: int) -> bytes:
    """Encode integer preserving lexicographic order using bias/offset encoding.

    Uses offset binary (also called excess-K or biased representation) to map
    the entire signed integer range to unsigned values that maintain numeric
    ordering when compared lexicographically as bytes.

    Strategy:
    - Add bias of 2^63 to shift entire range to non-negative
    - More negative → smaller biased value → smaller bytes
    - More positive → larger biased value → larger bytes
    - Encode as unsigned 64-bit big-endian

    This naturally preserves ordering without bit manipulation.

    Examples (conceptual):
        -2^63     → 0x0000000000000000 (smallest)
        -2        → 0x7FFFFFFFFFFFFFFE
        -1        → 0x7FFFFFFFFFFFFFFF
        0         → 0x8000000000000000
        1         → 0x8000000000000001
        2^63-1    → 0xFFFFFFFFFFFFFFFF (largest)

    Args:
        value: Integer to encode

    Returns:
        Encoded bytes (8 bytes total, unsigned big-endian)

    Raises:
        IntegerOverflowError: If integer is outside int64 range
    """
    if not (_INT64_MIN <= value <= _INT64_MAX):
        raise IntegerOverflowError(value, _INT64_MIN, _INT64_MAX)

    # Bias encoding: shift entire range to non-negative
    # This naturally preserves ordering: smaller values → smaller biased values
    biased_value = value + _INT64_BIAS

    # Encode as unsigned 64-bit big-endian
    return biased_value.to_bytes(8, byteorder="big", signed=False)


def _decode_integer(data: bytes, offset: int) -> tuple[int, int]:
    """Decode integer from binary data using bias/offset encoding.

    Args:
        data: Binary data containing encoded integer
        offset: Starting position in data

    Returns:
        Tuple of (decoded_value, bytes_consumed)

    Raises:
        DecodeError: If data is insufficient or invalid
    """
    if len(data) - offset < 8:  # Need 8 bytes for uint64
        raise DecodeError(f"Insufficient bytes for integer at offset {offset}")

    int_bytes = data[offset : offset + 8]

    # Decode as unsigned 64-bit big-endian
    biased_value = int.from_bytes(int_bytes, byteorder="big", signed=False)

    # Remove bias to get original signed value
    value = biased_value - _INT64_BIAS

    return value, 8


def _encode_string(value: str) -> bytes:
    """Encode string to UTF-8 bytes.

    No escaping needed since separator (0xFF) is invalid in UTF-8.

    Args:
        value: String to encode

    Returns:
        UTF-8 encoded bytes

    Raises:
        EncodeError: If string contains invalid UTF-8
    """
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError as e:
        raise EncodeError(f"Invalid UTF-8 in string: {e}") from e


def _decode_string(data: bytes) -> str:
    """Decode UTF-8 string from bytes.

    No unescaping needed since separator (0xFF) is invalid in UTF-8.

    Args:
        data: Encoded string bytes

    Returns:
        Decoded string

    Raises:
        DecodeError: If data contains invalid UTF-8
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise DecodeError(f"Invalid UTF-8 in encoded string: {e}") from e


class PyBinaryKeyCodec(KeyCodec[EncodedBinaryKey]):
    """Binary key codec that preserves lexicographic ordering for KV storage.

    This codec encodes tuple keys into binary format while maintaining the
    natural sort order of the original tuples. It supports mixed integer
    and string components.

    Key features:
    - Preserves lexicographic ordering for both integers and strings
    - Handles negative integers correctly using bias/offset encoding
    - Efficient binary encoding with type safety
    - Uses invalid UTF-8 byte (0xFF) as separator - no escaping needed
    - Trailing separator ensures prefix-based range queries work correctly

    Integer encoding:
    - Uses bias/offset encoding (excess-2^63 representation)
    - Maps signed int64 range to unsigned for natural byte ordering
    - 8 bytes per integer (unsigned big-endian)

    Encoding format:
    - Each component: TYPE_MARKER + ENCODED_VALUE + SEPARATOR
    - Integers: TYPE_INT (0x01) + 8_BYTES + SEPARATOR (0xFF)
    - Strings: TYPE_STR (0x02) + UTF8_BYTES + SEPARATOR (0xFF)
    - Trailing separator after last component

    Type ordering:
    - TYPE_INT (0x01) < TYPE_STR (0x02) ensures integers sort before strings

    Example:
        >>> codec = BinaryKeyCodec()
        >>> key = ("users", 42, "profile")
        >>> encoded = codec.encode(key)
        >>> decoded = codec.decode(encoded)
        >>> assert decoded == key
        >>>
        >>> # Negative integers work correctly
        >>> k1 = ("balance", -100)
        >>> k2 = ("balance", 50)
        >>> assert (k1 < k2) == (codec.encode(k1) < codec.encode(k2))
    """

    def encode(self, key: Key) -> EncodedBinaryKey:
        """Encode tuple key into binary format preserving lexicographic order.

        Args:
            key: Tuple containing strings and/or integers

        Returns:
            Binary encoded key with trailing separator

        Raises:
            EncodeError: If key structure is invalid
            IntegerOverflowError: If integer is outside supported range
        """
        # validate_key(key)

        parts: list[bytes] = []

        for i, component in enumerate(key):
            if isinstance(component, int):
                parts.extend([_TYPE_INT, _encode_integer(component), _SEPARATOR])
            elif isinstance(component, str):
                parts.extend([_TYPE_STR, _encode_string(component), _SEPARATOR])
            else:
                # This should never happen due to validate_key, but be defensive
                raise EncodeError(
                    f"Unsupported component type at index {i}: {type(component).__name__}"
                )

        # Parts already include trailing separator after each component
        return b"".join(parts)

    def decode(self, encoded: EncodedBinaryKey) -> Key:
        """Decode binary data back to original tuple key.

        Args:
            encoded: Previously encoded binary key

        Returns:
            Original tuple key

        Raises:
            DecodeError: If data is invalid or corrupted
        """
        if not isinstance(encoded, bytes):
            raise DecodeError(f"Expected bytes, got {type(encoded).__name__}")

        if not encoded:
            raise DecodeError("Empty encoded key")

        result: list[int | str] = []
        pos = 0

        while pos < len(encoded):
            # Read type marker
            if pos >= len(encoded):
                raise DecodeError("Unexpected end of data while reading type marker")

            type_marker = encoded[pos : pos + 1]
            pos += 1

            if type_marker == _TYPE_INT:
                # Decode integer (8 bytes with bias encoding)
                value, consumed = _decode_integer(encoded, pos)
                result.append(value)
                pos += consumed

                # Expect separator
                if pos >= len(encoded) or encoded[pos : pos + 1] != _SEPARATOR:
                    raise DecodeError(f"Missing separator after integer at position {pos}")
                pos += 1

            elif type_marker == _TYPE_STR:
                # Find next separator (no escaping needed - 0xFF is invalid UTF-8)
                sep_pos = encoded.find(_SEPARATOR, pos)

                if sep_pos == -1:
                    raise DecodeError(f"Missing separator after string at position {pos}")

                str_data = encoded[pos:sep_pos]
                result.append(_decode_string(str_data))
                pos = sep_pos + 1

            else:
                raise DecodeError(f"Invalid type marker at position {pos - 1}: {type_marker!r}")

        return tuple(result)


__all__ = [
    "PyBinaryKeyCodec",
]
