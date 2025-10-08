"""JSON codec adapter - text-based serialization with base64 encoding for bytes."""

from __future__ import annotations

import base64
import json
from typing import Any

from ..protocols import ValueCodecProtocol
from .exceptions import DecodeError, EncodeError
from .types import JSONEncoded, JSONSupportedValues


__all__ = ["JSONCodec"]


class JSONCodec(ValueCodecProtocol[JSONSupportedValues, JSONEncoded]):
    """
    Codec using JSON for human-readable serialization.

    This codec provides text-based serialization suitable for debugging,
    configuration files, and APIs. Binary data (bytes) is encoded using
    base64 to maintain JSON compatibility.

    Type Parameters:
        JSONValue: None, bytes, bool, int, float, str, list, or dict
        JSONEncoded: str (JSON text format)

    Features:
        - Human-readable output
        - Base64 encoding for binary data
        - Recursive handling of nested structures
        - Special markers for bytes (__bytes__) and tuples (__tuple__)

    Performance:
        The encode/decode operations perform recursive preprocessing/postprocessing
        to handle bytes and other special types that JSON doesn't natively support.
    """

    __slots__ = ()

    def encode(self, value: JSONSupportedValues) -> JSONEncoded:
        """
        Encode a value to JSON string with base64 for bytes.

        Args:
            value: The value to encode

        Returns:
            JSON string representation

        Raises:
            EncodeError: If encoding fails
        """
        try:
            processed = self._preprocess_encode(value)
            return json.dumps(processed)
        except Exception as e:
            msg = f"Failed to encode value: {e}"
            raise EncodeError(msg) from e

    def decode(self, encoded: JSONEncoded) -> JSONSupportedValues:
        """
        Decode a JSON string to value, handling bytes.

        Args:
            encoded: JSON string to decode

        Returns:
            Decoded value

        Raises:
            DecodeError: If decoding fails
        """
        try:
            parsed = json.loads(encoded)
            return self._postprocess_decode(parsed)
        except Exception as e:
            msg = f"Failed to decode value: {e}"
            raise DecodeError(msg) from e

    def _preprocess_encode(self, value: Any) -> Any:
        """
        Recursively preprocess value for JSON encoding.

        Converts bytes to base64-encoded dict markers and handles
        nested structures recursively.

        Args:
            value: Value to preprocess

        Returns:
            Preprocessed value safe for JSON encoding
        """
        if isinstance(value, bytes):
            return {"__bytes__": base64.b64encode(value).decode("ascii")}

        if isinstance(value, dict):
            return {k: self._preprocess_encode(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._preprocess_encode(item) for item in value]

        if isinstance(value, tuple):
            return {"__tuple__": [self._preprocess_encode(item) for item in value]}

        return value

    def _postprocess_decode(self, value: Any) -> Any:
        """
        Recursively postprocess value after JSON decoding.

        Restores bytes from base64 dict markers and handles
        nested structures recursively.

        Args:
            value: Value to postprocess

        Returns:
            Postprocessed value with bytes and tuples restored
        """
        if isinstance(value, dict):
            # Check for special byte marker
            if len(value) == 1 and "__bytes__" in value:
                return base64.b64decode(value["__bytes__"])

            # Check for special tuple marker
            if len(value) == 1 and "__tuple__" in value:
                items = [self._postprocess_decode(item) for item in value["__tuple__"]]
                return tuple(items)

            # Process regular dict
            return {k: self._postprocess_decode(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._postprocess_decode(item) for item in value]

        return value
