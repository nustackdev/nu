from __future__ import annotations

import base64
import json
from typing import Any

import attrs
from loomi import ResourceSpec
from loomistd.service import SyncService

from .._exceptions import DecodeError, EncodeError
from .constants import PATH_SEPARATOR
from .types import JSONCodecEncodedKey, JSONCodecEncodedValue, JSONCodecKey, JSONCodecValue


__all__ = [
    "JSONCodec",
    "JSONCodecSpec",
]


class JSONCodec(SyncService):
    """String and bytes codec using JSON for values with base64 encoding for binary data."""

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
        # Convert bytes parts to base64
        processed_key = []
        for part in key:
            if isinstance(part, bytes):
                # Encode bytes to base64 and prefix with 'b:' to identify it
                encoded_part = f"b:{base64.b64encode(part).decode('ascii')}"
                processed_key.append(encoded_part)
            else:
                # Ensure part is a string
                str_part = str(part)
                if PATH_SEPARATOR in str_part:
                    raise EncodeError(
                        f"Key part '{str_part}' contains invalid character. "
                        f"Keys should not contain PATH_SEPARATOR: <{PATH_SEPARATOR}>"
                    )
                processed_key.append(str_part)

        try:
            return PATH_SEPARATOR.join(processed_key)
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
            parts = encoded.split(PATH_SEPARATOR)
            decoded_parts = []

            for part in parts:
                if part.startswith("b:"):
                    # This is a base64-encoded bytes part
                    try:
                        # Remove the 'b:' prefix and decode
                        bytes_data = base64.b64decode(part[2:])
                        decoded_parts.append(bytes_data)
                    except Exception as e:
                        raise DecodeError(f"Failed to decode bytes in key part: {e}")
                else:
                    # Regular string part
                    decoded_parts.append(part)

            return tuple(decoded_parts)
        except Exception as e:
            raise DecodeError(f"Failed to decode key: {e}")

    def encode_value(self, value: JSONCodecValue) -> JSONCodecEncodedValue:
        """
        Convert value to JSON string, handling bytes with base64 encoding.

        Args:
            value: Value to encode

        Returns:
            JSON string representation of value

        Raises:
            EncodeError: If value cannot be encoded
        """
        try:
            # Pre-process the value to handle bytes
            processed_value = self._preprocess_value_for_encoding(value)
            return json.dumps(processed_value)
        except Exception as e:
            raise EncodeError(f"Failed to encode value: {e}")

    def decode_value(self, encoded: JSONCodecEncodedValue) -> JSONCodecValue:
        """
        Convert JSON string back to value, handling bytes.

        Args:
            encoded: Value to decode

        Returns:
            Original value

        Raises:
            DecodeError: If value cannot be decoded
        """
        try:
            parsed_json = json.loads(encoded)
            # Post-process to convert back any bytes
            return self._postprocess_value_after_decoding(parsed_json)
        except Exception as e:
            raise DecodeError(f"Failed to decode value: {e}")

    def _preprocess_value_for_encoding(self, value: Any) -> Any:
        """
        Recursively preprocess a value to handle bytes before JSON encoding.

        Args:
            value: The value to preprocess

        Returns:
            The preprocessed value with bytes converted to a special format
        """
        if isinstance(value, bytes):
            # For bytes, encode to base64 and return as a dict with a special key
            return {"__bytes__": base64.b64encode(value).decode("ascii")}
        elif isinstance(value, dict):
            # For dictionaries, process each key-value pair
            return {k: self._preprocess_value_for_encoding(v) for k, v in value.items()}
        elif isinstance(value, list):
            # For lists, process each item
            return [self._preprocess_value_for_encoding(item) for item in value]
        elif isinstance(value, tuple):
            # For tuples, convert to list, process each item, and mark as tuple
            processed = [self._preprocess_value_for_encoding(item) for item in value]
            return {"__tuple__": processed}
        else:
            # Return the value as is for JSON-serializable types
            return value

    def _postprocess_value_after_decoding(self, value: Any) -> Any:
        """
        Recursively postprocess a value after JSON decoding to restore bytes.

        Args:
            value: The value to postprocess

        Returns:
            The postprocessed value with bytes restored
        """
        if isinstance(value, dict):
            # Check if this is our special bytes format
            if len(value) == 1 and "__bytes__" in value:
                return base64.b64decode(value["__bytes__"])
            # Check if this is our special tuple format
            elif len(value) == 1 and "__tuple__" in value:
                processed_items = [
                    self._postprocess_value_after_decoding(item) for item in value["__tuple__"]
                ]
                return tuple(processed_items)
            # Otherwise process each key-value pair in the dictionary
            return {k: self._postprocess_value_after_decoding(v) for k, v in value.items()}
        elif isinstance(value, list):
            # For lists, process each item
            return [self._postprocess_value_after_decoding(item) for item in value]
        else:
            # Return other values as is
            return value


@attrs.define(frozen=True, slots=True, kw_only=True)
class JSONCodecSpec(ResourceSpec):
    name: str = "json_codec"
    factory: type = JSONCodec
