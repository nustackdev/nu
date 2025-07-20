from __future__ import annotations

from typing import Protocol, TypeVar

__all__ = [
    "CodecProtocol",
]

CodecKeyT = TypeVar("CodecKeyT")
CodecValueT = TypeVar("CodecValueT")
CodecEncodedKeyT = TypeVar("CodecEncodedKeyT")
CodecEncodedValueT = TypeVar("CodecEncodedValueT")


class CodecProtocol(Protocol[CodecKeyT, CodecValueT, CodecEncodedKeyT, CodecEncodedValueT]):
    """
    Protocol defining data encoding/decoding.

    Codec implementations handle:
    - Key serialization
    - Value serialization
    - Type validation
    - Format conversion

    Type Parameters:
        KeyT: Key type (must be tuple of strings)
        ValueT: Value type (must be valid state value)
        EncodedKeyT: Encoded key type
        EncodedValueT: Encoded value type

    Implementation Requirements:
        - Must maintain roundtrip consistency
        - Must validate all data
        - Must handle all value types
        - Must be thread-safe
    """

    def encode_key(self, key: CodecKeyT) -> CodecEncodedKeyT:
        """
        Encode key for storage.

        This method must:
        - Validate key format
        - Convert to storage format
        - Maintain ordering

        Args:
            key: Key to encode

        Returns:
            Encoded key

        Raises:
            EncodeError: If encoding fails
            ValueError: If key format invalid
        """
        ...

    def decode_key(self, encoded: CodecEncodedKeyT) -> CodecKeyT:
        """
        Decode key from storage.

        This method must:
        - Validate encoded format
        - Convert to key tuple
        - Preserve ordering

        Args:
            encoded: Encoded key to decode

        Returns:
            Decoded key tuple

        Raises:
            DecodeError: If decoding fails
            ValueError: If encoded format invalid
        """
        ...

    def encode_value(self, value: CodecValueT) -> CodecEncodedValueT:
        """
        Encode value for storage.

        This method must:
        - Validate value type
        - Handle all value variants
        - Convert to storage format

        Args:
            value: Value to encode

        Returns:
            Encoded value

        Raises:
            EncodeError: If encoding fails
            ValueError: If value type invalid
            TypeError: If value contains unsupported types
        """
        ...

    def decode_value(self, encoded: CodecEncodedValueT) -> CodecValueT:
        """
        Decode value from storage.

        This method must:
        - Validate encoded format
        - Convert to appropriate type
        - Maintain type safety

        Args:
            encoded: Encoded value to decode

        Returns:
            Decoded value

        Raises:
            DecodeError: If decoding fails
            ValueError: If encoded format invalid
            TypeError: If encoded value contains invalid types
        """
        ...
