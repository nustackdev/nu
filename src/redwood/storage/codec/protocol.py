"""Protocol definitions for coddec, storage, and observer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from redwood.loc import key
    from redwood.types import Value


__all__ = [
    "CodecProtocol",
    "KeyCodecProtocol",
    "ValueCodecProtocol",
]


class CodecProtocol[EncodedKeyT, EncodedValueT](Protocol):
    """Protocol for complete storage encoding/decoding.

    Combines key and value codec operations into a unified interface
    for storage engines that need to encode both keys and values.

    Type Parameters:
        KeyT: The type of keys (contravariant)
        EncodedKeyT: The type of encoded keys (covariant)
        ValueT: The type of values (contravariant)
        EncodedValueT: The type of encoded values (covariant)
    """

    def encode_key(self, key: key.Key) -> EncodedKeyT:
        """Encode a key for storage.

        Args:
            key: The key to encode

        Returns:
            Encoded key

        Raises:
            EncodeError: If encoding fails
        """
        ...

    def decode_key(self, encoded: EncodedKeyT) -> key.Key:
        """Decode a key from storage.

        Args:
            encoded: Encoded key to decode

        Returns:
            Decoded key

        Raises:
            DecodeError: If decoding fails
        """
        ...

    def encode_value(self, value: Value) -> EncodedValueT:
        """Encode a value for storage.

        Args:
            value: The value to encode

        Returns:
            Encoded value

        Raises:
            EncodeError: If encoding fails
        """
        ...

    def decode_value(self, encoded: EncodedValueT) -> Value:
        """Decode a value from storage.

        Args:
            encoded: Encoded value to decode

        Returns:
            Decoded value

        Raises:
            DecodeError: If decoding fails
        """
        ...


class KeyCodecProtocol[EncodedKeyT](Protocol):
    """Protocol for encoding/decoding storage keys.

    Type Parameters:
        KeyT: The type of keys that can be encoded (contravariant)
        EncodedKeyT: The type of encoded keys (covariant)

    Keys typically require lexicographic ordering preservation for
    range queries and efficient prefix scans in storage engines.
    """

    def encode(self, key: key.Key) -> EncodedKeyT:
        """Encode a key for storage.

        Args:
            key: The key to encode

        Returns:
            Encoded key suitable for storage

        Raises:
            EncodeError: If encoding fails
            ValueError: If key type is invalid
        """
        ...

    def decode(self, encoded: EncodedKeyT) -> key.Key:
        """Decode a key from storage.

        Args:
            encoded: Encoded key to decode

        Returns:
            Decoded key

        Raises:
            DecodeError: If decoding fails
            ValueError: If encoded format is invalid
        """
        ...


class ValueCodecProtocol[EncodedValueT](Protocol):
    """Protocol for encoding/decoding storage values.

    Type Parameters:
        ValueT: The type of values that can be encoded (contravariant)
        EncodedValueT: The type of encoded values (covariant)
    """

    def encode(self, value: Value) -> EncodedValueT:
        """Encode a value for storage.

        Args:
            value: The value to encode

        Returns:
            Encoded value suitable for storage

        Raises:
            EncodeError: If encoding fails
            ValueError: If value type is invalid
            TypeError: If value contains unsupported types
        """
        ...

    def decode(self, encoded: EncodedValueT) -> Value:
        """Decode a value from storage.

        Args:
            encoded: Encoded value to decode

        Returns:
            Decoded value

        Raises:
            DecodeError: If decoding fails
            ValueError: If encoded format is invalid
            TypeError: If encoded value contains invalid types
        """
        ...
