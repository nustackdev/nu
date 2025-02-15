from __future__ import annotations

import json

from loomi.service import SyncService

from .._exceptions import DecodeError, EncodeError
from .constants import PATH_SEPARATOR
from .types import JSONCodecEncodedKey, JSONCodecEncodedValue, JSONCodecKey, JSONCodecValue

__all__ = [
    "JSONCodec",
]


class JSONCodec(SyncService):
    """Simple string-based codec using JSON for values."""

    def encode_key(self, key: JSONCodecKey) -> JSONCodecEncodedKey:
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

    def decode_key(self, encoded: JSONCodecEncodedKey) -> JSONCodecKey:
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

    def encode_value(self, value: JSONCodecValue) -> JSONCodecEncodedValue:
        """
        Convert value to JSON string.

        Args:
            value: Value to encode

        Returns:
            JSON string representation of value

        Raises:
            EncodeError: If key cannot be encoded
        """
        try:
            return json.dumps(value)
        except Exception as e:
            raise EncodeError(f"Failed to encode value: {e}")

    def decode_value(self, encoded: JSONCodecEncodedValue) -> JSONCodecValue:
        """
        Convert JSON string back to value.

        Args:
            encoded: Value to decode

        Returns:
            Original value

        Raises:
            DecodeError: If key cannot be decoded
        """
        try:
            return json.loads(encoded)
        except Exception as e:
            raise DecodeError(f"Failed to decode value: {e}")
