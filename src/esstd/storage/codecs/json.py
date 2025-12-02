"""JSON codec adapter - text-based serialization with base64 encoding for bytes."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.storage import ValueCodecProtocol
    from everyshape.types import Value


__all__ = ["JSONCodec"]


class JSONCodec:
    """Codec using JSON for human-readable serialization.

    This codec provides text-based serialization suitable for debugging,
    configuration files, and APIs. Binary data (bytes) is encoded using
    base64 to maintain JSON compatibility.


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

    def encode(self, value: Value) -> str:
        """Encode a value to JSON string with base64 for bytes.

        Args:
            value: The value to encode

        Returns:
            JSON string representation
        """
        processed = self._preprocess_encode(value)
        return json.dumps(processed)

    def decode(self, encoded: str) -> Value:
        """Decode a JSON string to value, handling bytes.

        Args:
            encoded: JSON string to decode

        Returns:
            Decoded value

        """
        parsed = json.loads(encoded)
        return self._postprocess_decode(parsed)

    def _preprocess_encode(self, value: Value) -> Value:
        """Recursively preprocess value for JSON encoding.

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

    def _postprocess_decode(self, value: Value) -> Value:
        """Recursively postprocess value after JSON decoding.

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


if TYPE_CHECKING:
    _: type[ValueCodecProtocol[str]] = JSONCodec
