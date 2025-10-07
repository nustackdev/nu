from __future__ import annotations

import base64
import json
from typing import Any

from .exceptions import DecodeError, EncodeError
from .types import JSONCodecEncodedValue, JSONCodecValue


__all__ = [
    "JSONCodec",
]


class JSONCodec:
    """String and bytes codec using JSON for values with base64 encoding for binary data."""

    def encode(self, value: JSONCodecValue) -> JSONCodecEncodedValue:
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
            raise EncodeError(f"Failed to encode value: {e}") from e

    def decode(self, encoded: JSONCodecEncodedValue) -> JSONCodecValue:
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
            raise DecodeError(f"Failed to decode value: {e}") from e

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
