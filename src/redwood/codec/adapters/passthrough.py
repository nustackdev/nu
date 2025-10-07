from __future__ import annotations

from .types import (
    PassthroughCodecEncodedValue,
    PassthroughCodecValue,
)


__all__ = [
    "PassthroughCodec",
]


class PassthroughCodec:
    """
    Codec that performs minimal transformation of data.
    Suitable for in-memory storage where serialization is not needed.
    """

    def encode_value(self, value: PassthroughCodecValue) -> PassthroughCodecEncodedValue:
        """
        Pass through value without transformation.

        Args:
            value: Value to encode

        Returns:
            Same value without modification
        """
        return value

    def decode_value(self, encoded: PassthroughCodecEncodedValue) -> PassthroughCodecValue:
        """
        Pass through value without transformation.

        Args:
            encoded: Value to decode

        Returns:
            Same value without modification
        """
        return encoded
