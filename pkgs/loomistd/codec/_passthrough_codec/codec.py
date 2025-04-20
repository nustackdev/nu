from __future__ import annotations

from loomi._service import SyncService

from .._exceptions import DecodeError, EncodeError
from .constans import PATH_SEPARATOR
from .types import (
    PassthroughCodecEncodedKey,
    PassthroughCodecEncodedValue,
    PassthroughCodecKey,
    PassthroughCodecValue,
)

__all__ = [
    "PassthroughCodec",
]


class PassthroughCodec(SyncService):
    """
    Codec that performs minimal transformation of data.
    Suitable for in-memory storage where serialization is not needed.
    """

    def encode_key(self, key: PassthroughCodecKey) -> PassthroughCodecEncodedKey:
        """
        Convert key to string representation.

        Args:
            key: Key to encode (tuple)

        Returns:
            String representation of key

        Raises:
            EncodeError: If key cannot be encoded
        """
        if any([PATH_SEPARATOR in part for part in key]):
            raise EncodeError(
                f"Key {key} contains invalid character. Keys should not contain PATH_SEPARATOR: <{PATH_SEPARATOR}>"
            )
        try:
            return PATH_SEPARATOR.join(key)
        except Exception as e:
            raise EncodeError(f"Failed to encode key: {e}")

    def decode_key(self, encoded: PassthroughCodecEncodedKey) -> PassthroughCodecKey:
        """
        Convert string back to key tuple.

        Args:
            encoded: String to decode

        Returns:
            Original key tuple

        Raises:
            DecodeError: If key cannot be decoded
        """
        try:
            return tuple(encoded.split(PATH_SEPARATOR))
        except Exception as e:
            raise DecodeError(f"Failed to decode key: {e}")

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
