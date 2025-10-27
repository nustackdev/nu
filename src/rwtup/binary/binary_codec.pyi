"""Type stubs for binary_key_codec Cython extension.

This stub file provides type hints for IDE support and static type checking.
"""

from ..types import Key

__all__ = [
    "BinaryKeyCodec",
    "DecodeError",
    "EncodeError",
    "IntegerOverflowError",
]

class IntegerOverflowError(Exception):
    """Raised when integer is outside int64 range [-2^63, 2^63-1]."""
    def __init__(self, message: str) -> None: ...

class EncodeError(Exception):
    """Raised when encoding fails due to invalid input."""
    def __init__(self, message: str) -> None: ...

class DecodeError(Exception):
    """Raised when decoding fails due to invalid or corrupted data."""
    def __init__(self, message: str) -> None: ...

class BinaryKeyCodec:
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
    - Range: -2^63 to 2^63-1 (int64)
    - 8 bytes per integer (unsigned big-endian)

    String encoding:
    - UTF-8 encoding
    - Length limits: 1 byte (non-empty) to 10MB
    - No escaping needed (0xFF separator is invalid UTF-8)

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

    def __init__(self) -> None:
        """Initialize the codec."""
        ...

    def encode(self, key: Key) -> bytes:
        """Encode tuple key into binary format preserving lexicographic order.

        Args:
            key: Tuple containing strings and/or integers. Must be non-empty.
                - Integers must be in range [-2^63, 2^63-1]
                - Strings must be non-empty and <= 10MB
                - Only int and str types are supported

        Returns:
            Binary encoded key as bytes with trailing separator.

        Raises:
            EncodeError: If key structure is invalid:
                - Empty tuple
                - Empty string component
                - String longer than 10MB
                - Invalid component type (not int or str)
                - Invalid UTF-8 in string
            IntegerOverflowError: If integer is outside int64 range
                [-2^63, 2^63-1] = [-9223372036854775808, 9223372036854775807]

        Example:
            >>> codec = BinaryKeyCodec()
            >>> encoded = codec.encode(("users", 123, "profile"))
            >>> isinstance(encoded, bytes)
            True
        """
        ...

    def decode(self, encoded: bytes) -> Key:
        """Decode binary data back to original tuple key.

        Args:
            encoded: Previously encoded binary key (bytes object).
                Must be valid encoded data from encode().

        Returns:
            Original tuple key with the same components that were encoded.

        Raises:
            DecodeError: If data is invalid or corrupted:
                - Empty encoded data
                - Invalid type marker
                - Missing separator
                - Insufficient bytes for integer
                - Invalid UTF-8 in string data
                - Unexpected end of data

        Example:
            >>> codec = BinaryKeyCodec()
            >>> encoded = codec.encode(("data", -42))
            >>> decoded = codec.decode(encoded)
            >>> decoded
            ('data', -42)
        """
        ...
