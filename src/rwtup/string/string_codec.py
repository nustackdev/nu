"""String key codec implementation for human-readable lexicographic ordering preservation.

This codec encodes tuple keys into a human-readable string format while maintaining
isomorphic ordering with byte-based codecs. The encoding uses visual type markers
and separators for easy inspection and debugging.

Format: [TYPE]VALUE.[TYPE]VALUE.
Example: [s]users.[i]p00042[+00042].[s]profile.

Note the trailing separator - this ensures prefix-based range queries work correctly.

Character restrictions:
    - Strings cannot contain: '.', '[', ']'
    - These characters are reserved for encoding structure
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ..exceptions import DecodeError, EncodeError, IntegerOverflowError


if TYPE_CHECKING:
    from ..types import EncodedStringKey, Key


# Encoding format constants
_TYPE_INT: Final[str] = "[i]"  # Integer type marker
_TYPE_STR: Final[str] = "[s]"  # String type marker
_SEPARATOR: Final[str] = "."  # Component separator (also used as trailing separator)
_FORBIDDEN_CHARS: Final[frozenset[str]] = frozenset({".", "[", "]"})

# Integer encoding configuration
# 5 decimal digits allows 100,000 distinct values in base-10
_INT_WIDTH: Final[int] = 5
_INT_MIN: Final[int] = -49999  # Symmetric signed range
_INT_MAX: Final[int] = 49999  # Total range: 99,999 values (fits in 5 digits)


def _validate_key(key: Key) -> None:
    """Validate that key is a non-empty tuple of strings and/or integers.

    Args:
        key: Key to validate

    Raises:
        EncodeError: If key structure is invalid
    """
    if not isinstance(key, tuple):
        raise EncodeError(f"Key must be a tuple, got {type(key).__name__}")

    if len(key) == 0:
        raise EncodeError("Key cannot be empty")

    for i, component in enumerate(key):
        if not isinstance(component, (int, str)):
            raise EncodeError(
                f"Key component at index {i} must be int or str, got {type(component).__name__}"
            )


def _validate_string_component(value: str, index: int) -> None:
    """Validate that string component doesn't contain forbidden characters.

    Args:
        value: String component to validate
        index: Position in key (for error messages)

    Raises:
        EncodeError: If string contains forbidden characters
    """
    for char in _FORBIDDEN_CHARS:
        if char in value:
            raise EncodeError(
                f"String component at index {index} contains forbidden character {char!r}. "
                f"Forbidden characters: {sorted(_FORBIDDEN_CHARS)}"
            )


def _format_integer_with_leading_zeros(value: int, width: int) -> str:
    """Format integer with leading zeros to specified width.

    Args:
        value: Non-negative integer to format
        width: Total width including leading zeros

    Returns:
        Zero-padded string representation
    """
    return str(value).zfill(width)


def _encode_integer(value: int) -> str:
    """Encode integer (including negatives) with ordering preservation and human readability.

    Uses bias encoding (offset binary) to map the entire integer range to non-negative
    values that maintain numeric ordering when compared lexicographically as strings.

    Format: {sign}{biased_value}[{original_value}]
    - Sign: 'n' for negative, 'p' for positive/zero (visual indicator only)
    - Biased value: value + abs(min) to shift into non-negative range
    - Original value: human-readable with sign (in brackets)

    The biased value naturally preserves ordering:
    - More negative → smaller biased value → smaller string
    - More positive → larger biased value → larger string

    Examples:
        -49999 → "n00000[-49999]"  (smallest biased value)
        -111   → "n49888[-00111]"
        -11    → "n49988[-00011]"
        0      → "p49999[+00000]"
        42     → "p50041[+00042]"
        49999  → "p99998[+49999]"  (largest biased value)

    Args:
        value: Integer to encode (must be in supported range)

    Returns:
        Encoded string with ordering prefix and human-readable suffix

    Raises:
        IntegerOverflowError: If integer is outside supported range
    """
    if not (_INT_MIN <= value <= _INT_MAX):
        raise IntegerOverflowError(value, _INT_MIN, _INT_MAX)

    # Bias encoding: shift entire range to non-negative
    # This naturally preserves ordering: smaller values → smaller biased values
    bias = abs(_INT_MIN)
    biased_value = value + bias

    # Sign prefix for human readability (not needed for ordering)
    # The biased value alone ensures correct lexicographic ordering
    sign_prefix = "n" if value < 0 else "p"

    # Format biased value with zero padding
    biased_str = _format_integer_with_leading_zeros(biased_value, _INT_WIDTH)

    # Format original value with sign for human readability
    original_str = f"{value:+06d}"  # Always show sign, zero-pad to 6 chars

    return f"{sign_prefix}{biased_str}[{original_str}]"


def _decode_integer(encoded: str) -> int:
    """Decode integer from encoded format back to original value.

    Extracts the human-readable original value from the bracketed suffix.

    Args:
        encoded: Encoded integer string

    Returns:
        Original integer value

    Raises:
        DecodeError: If format is invalid
    """
    # Find the bracketed original value
    bracket_start = encoded.find("[")
    bracket_end = encoded.find("]")

    if bracket_start == -1 or bracket_end == -1:
        raise DecodeError(f"Invalid integer format: missing brackets in {encoded!r}")

    if bracket_end != len(encoded) - 1:
        raise DecodeError(
            f"Invalid integer format: unexpected data after closing bracket in {encoded!r}"
        )

    # Extract and parse the original value
    original_str = encoded[bracket_start + 1 : bracket_end]

    try:
        result = int(original_str)
    except ValueError as e:
        raise DecodeError(f"Invalid integer in brackets: {original_str!r}") from e

    # Validate range
    if not (_INT_MIN <= result <= _INT_MAX):
        raise DecodeError(f"Integer {result} outside valid range")

    return result


class StringKeyCodec:
    """Human-readable string key codec that preserves lexicographic ordering.

    This codec encodes tuple keys into human-readable string format while
    maintaining isomorphic ordering with byte-based encodings. It's designed
    for debugging, logging, and toy examples where human readability matters.

    Key features:
    - Human-readable output with visual type markers: [s] and [i]
    - Preserves lexicographic ordering (isomorphic to byte codec ordering)
    - Signed integers with clever encoding: both correct ordering AND readable
    - No escaping needed - uses character restrictions instead
    - Trailing separator for correct prefix-based range queries

    Integer encoding:
    - Supports both negative and positive integers in configured range
    - Format: {sign}{biased}[{original}] where biased ensures order, original shows value
    - Example: -42 → "n49957[-00042]" (orders correctly, reads as -42)
    - Uses bias/offset encoding: all values shifted by abs(min) to non-negative range

    String constraints:
    - Cannot contain: '.', '[', ']'
    - These characters are reserved for encoding structure

    Encoding format:
    - Each component: [TYPE_MARKER]VALUE
    - Components separated by '.'
    - Trailing '.' after last component (essential for prefix searches)
    - Integers: [i]p00042[+00042].
    - Strings: [s]users.

    Ordering properties:
    - String sorting: lexicographic comparison preserved
    - Integer sorting: biased encoding ensures numeric order in string space
    - Negative integers: correctly sort before positive (using 'n' < 'p' prefix)
    - Mixed types: integers sort before strings ([i] < [s] in ASCII)
    - Isomorphism: if bytes_encode(k1) < bytes_encode(k2), then
      string_encode(k1) < string_encode(k2)

    Trailing separator rationale:
    - Without it: ("foo",) → "[s]foo" and ("foobar",) → "[s]foobar"
      would cause "[s]foo" < "[s]foobar" < "[s]foo.[s]x"
    - With it: ("foo",) → "[s]foo." and ("foobar",) → "[s]foobar."
      gives "[s]foo." < "[s]foo.[s]x." < "[s]foobar."
    - This ensures prefix-based range queries work correctly

    Example:
        >>> codec = StringKeyCodec()
        >>> key = ("users", 42, "profile")
        >>> encoded = codec.encode(key)
        >>> print(encoded)
        [s]users.[i]p00042[+00042].[s]profile.
        >>> decoded = codec.decode(encoded)
        >>> assert decoded == key
        >>>
        >>> # Negative integers work too
        >>> codec.encode(("balance", -100))
        '[s]balance.[i]n49899[-00100].'
        >>>
        >>> # Ordering is preserved
        >>> k1 = ("users", -50)
        >>> k2 = ("users", 100)
        >>> assert (k1 < k2) == (codec.encode(k1) < codec.encode(k2))
    """

    def encode(self, key: Key) -> EncodedStringKey:
        """Encode tuple key into human-readable string format.

        The encoding preserves lexicographic ordering, meaning that if one key
        would sort before another in their natural tuple form, their encoded
        strings will maintain that same ordering.

        Args:
            key: Tuple containing strings and/or integers

        Returns:
            Human-readable encoded string with trailing separator

        Raises:
            EncodeError: If key structure is invalid or string contains forbidden chars
            IntegerOverflowError: If integer is outside supported range

        Example:
            >>> codec = StringKeyCodec()
            >>> codec.encode(("users", 42))
            '[s]users.[i]p00042[+00042].'
            >>> codec.encode(("admin", -5, "settings"))
            '[s]admin.[i]n49994[-00005].[s]settings.'
        """
        _validate_key(key)

        parts: list[str] = []

        for i, component in enumerate(key):
            if isinstance(component, int):
                # Encode integer with type marker and special signed encoding
                encoded_int = _encode_integer(component)
                parts.append(f"{_TYPE_INT}{encoded_int}")

            elif isinstance(component, str):
                # Validate string doesn't contain forbidden characters
                _validate_string_component(component, i)
                parts.append(f"{_TYPE_STR}{component}")

            else:
                # This should never happen due to _validate_key, but be defensive
                raise EncodeError(
                    f"Unsupported component type at index {i}: {type(component).__name__}"
                )

        # Join all components with separator and add trailing separator
        # The trailing separator is essential for correct prefix-based range queries
        return _SEPARATOR.join(parts) + _SEPARATOR

    def decode(self, encoded: EncodedStringKey) -> Key:
        """Decode string data back to original tuple key.

        Args:
            encoded: Previously encoded string key

        Returns:
            Original tuple key

        Raises:
            DecodeError: If data is invalid or corrupted

        Example:
            >>> codec = StringKeyCodec()
            >>> codec.decode("[s]users.[i]p00042[+00042].")
            ('users', 42)
            >>> codec.decode("[s]admin.[i]n49994[-00005].[s]settings.")
            ('admin', -5, 'settings')
        """
        if not isinstance(encoded, str):
            raise DecodeError(f"Expected str, got {type(encoded).__name__}")

        if not encoded:
            raise DecodeError("Empty encoded key")

        # Remove trailing separator if present
        if encoded.endswith(_SEPARATOR):
            encoded = encoded[:-1]

        if not encoded:
            raise DecodeError("Encoded key contains only separator")

        # Split on separator to get individual components
        parts = encoded.split(_SEPARATOR)
        result: list[int | str] = []

        for i, part in enumerate(parts):
            if not part:
                raise DecodeError(f"Empty component at index {i}")

            # Check for integer type marker
            if part.startswith(_TYPE_INT):
                # Extract integer value after type marker
                int_encoded = part[len(_TYPE_INT) :]
                value = _decode_integer(int_encoded)
                result.append(value)

            # Check for string type marker
            elif part.startswith(_TYPE_STR):
                # Extract string value after type marker
                str_value = part[len(_TYPE_STR) :]
                result.append(str_value)

            else:
                raise DecodeError(
                    f"Invalid type marker at index {i}: component must start with "
                    f"{_TYPE_INT} or {_TYPE_STR}, got {part[:3]!r}"
                )

        return tuple(result)


__all__ = [
    "StringKeyCodec",
]
