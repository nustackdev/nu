from __future__ import annotations

from typing import Protocol, TypeVar


SupportedValuesT = TypeVar("SupportedValuesT")
CodecEncodedValueT = TypeVar("CodecEncodedValueT")


__all__ = [
    "ValueCodecProtocol",
]


class ValueCodecProtocol(Protocol[SupportedValuesT, CodecEncodedValueT]):
    """
    Protocol defining data encoding/decoding.

    """

    def encode(self, value: SupportedValuesT) -> CodecEncodedValueT:
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

    def decode(self, encoded: CodecEncodedValueT) -> SupportedValuesT:
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
