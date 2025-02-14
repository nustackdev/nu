from __future__ import annotations

import struct
from typing import Any

from loomi.service import SyncService

from .._exceptions import DecodeError, EncodeError
from .constants import (
    DOUBLE_STRUCT,
    INT64_STRUCT,
    MAX_COLLECTION_SIZE,
    MAX_DEPTH,
    MAX_STR_SIZE,
    PATH_SEPARATOR,
    TYPE_BYTES,
    TYPE_DICT,
    TYPE_END,
    TYPE_FALSE,
    TYPE_FLOAT,
    TYPE_INT,
    TYPE_LIST,
    TYPE_MARKERS,
    TYPE_NONE,
    TYPE_STR,
    TYPE_TRUE,
    UINT32_STRUCT,
)
from .types import (
    BinaryCodecEncodedKey,
    BinaryCodecEncodedValue,
    BinaryCodecKey,
    BinaryCodecValue,
    DecoderState,
)


class BinaryCodec(SyncService):
    """
    Optimized binary codec implementation with nested structure support.

    Features:
    - Explicit handling of nested structures with depth tracking
    - Memory usage limits
    - Performance optimizations for large datasets
    - Detailed error messages without exception wrapping
    """

    def encode_key(self, key: BinaryCodecKey) -> BinaryCodecEncodedKey:
        """Encode key tuple into bytes with lexicographical ordering."""
        if not isinstance(key, tuple):
            raise EncodeError("Key must be a tuple")

        parts = bytearray()

        for part in key:
            if isinstance(part, str):
                try:
                    encoded = part.encode("utf-8")
                    if not encoded:
                        raise EncodeError("Empty string not allowed in key")
                    if PATH_SEPARATOR in encoded:
                        raise EncodeError("Key string contains forbidden byte sequence")
                    if len(encoded) > MAX_STR_SIZE:
                        raise EncodeError(f"Key string too large: {len(encoded)} bytes")
                    parts.extend(encoded)

                except UnicodeEncodeError:
                    raise EncodeError("Key string contains invalid UTF-8")

            elif isinstance(part, int):
                if not (-(2**63) <= part < 2**63):
                    raise EncodeError("Integer key out of range")
                parts.extend(PATH_SEPARATOR)
                parts.extend(INT64_STRUCT.pack(part))

            else:
                raise EncodeError(f"Key parts must be str or int, got {type(part)}")

            parts.extend(PATH_SEPARATOR)

        return bytes(parts[:-1])  # Remove trailing separator

    def decode_key(self, encoded: BinaryCodecEncodedKey) -> BinaryCodecKey:
        """Decode bytes back to key tuple."""
        if not isinstance(encoded, bytes):
            raise DecodeError(f"Expected bytes, got {type(encoded)}")

        parts = encoded.split(PATH_SEPARATOR)
        result: list[str] = []

        for part in parts:
            if not part:
                continue

            # Check for int marker (exactly 8 bytes)
            # if len(part) == 8:
            #     try:
            #         value = INT64_STRUCT.unpack(part)[0]
            #         result.append(value)
            #         continue
            #     except struct.error:
            #         raise DecodeError("Invalid integer encoding in key")

            # Decode as UTF-8 string
            try:
                if len(part) > MAX_STR_SIZE:
                    raise DecodeError(f"Key string too large: {len(part)} bytes")
                result.append(part.decode("utf-8"))
            except UnicodeDecodeError:
                raise DecodeError("Invalid UTF-8 in key string")

        return tuple(result)

    def encode_value(self, value: BinaryCodecValue) -> BinaryCodecEncodedValue:
        """Encode value into bytes with nested structure support."""
        return self._encode_value_impl(value, 0)

    def decode_value(self, encoded: BinaryCodecEncodedValue) -> BinaryCodecValue:
        """Decode value from bytes with nested structure support."""
        return self._decode_value_impl(encoded, 0)

    def _encode_size(self, size: int) -> bytes:
        """Encode size value with range check."""
        if not 0 <= size <= 0xFFFFFFFF:
            raise EncodeError(f"Size out of range: {size}")
        return UINT32_STRUCT.pack(size)

    def _encode_container(
        self, value: list[Any] | dict[str, Any], depth: int, type_marker: int
    ) -> bytes:
        """Encode list or dict with depth tracking."""
        if depth >= MAX_DEPTH:
            raise EncodeError(f"Maximum nesting depth ({MAX_DEPTH}) exceeded")

        if len(value) > MAX_COLLECTION_SIZE:
            raise EncodeError(f"Collection too large: {len(value)} items")

        parts = bytearray(TYPE_MARKERS[type_marker])

        if isinstance(value, list):
            for item in value:
                encoded = self.encode_value(item)
                parts.extend(self._encode_size(len(encoded)))
                parts.extend(encoded)

        else:  # dict
            for k, v in value.items():
                if not isinstance(k, str):
                    raise EncodeError(f"Dict keys must be strings, got {type(k)}")

                key_encoded = self.encode_value(k)
                val_encoded = self.encode_value(v)

                parts.extend(self._encode_size(len(key_encoded)))
                parts.extend(key_encoded)
                parts.extend(self._encode_size(len(val_encoded)))
                parts.extend(val_encoded)

        parts.extend(TYPE_MARKERS[TYPE_END])
        return bytes(parts)

    def _encode_value_impl(self, value: BinaryCodecValue, depth: int) -> BinaryCodecEncodedValue:
        if value is None:
            return TYPE_MARKERS[TYPE_NONE]

        elif isinstance(value, bool):
            return TYPE_MARKERS[TYPE_TRUE] if value else TYPE_MARKERS[TYPE_FALSE]

        elif isinstance(value, int):
            if not (-(2**63) <= value < 2**63):
                raise EncodeError("Integer out of range")
            return TYPE_MARKERS[TYPE_INT] + INT64_STRUCT.pack(value)

        elif isinstance(value, float):
            try:
                return TYPE_MARKERS[TYPE_FLOAT] + DOUBLE_STRUCT.pack(value)
            except struct.error:
                raise EncodeError("Invalid float value")

        elif isinstance(value, str):
            try:
                encoded = value.encode("utf-8")
                if len(encoded) > MAX_STR_SIZE:
                    raise EncodeError(f"String too large: {len(encoded)} bytes")
                return TYPE_MARKERS[TYPE_STR] + self._encode_size(len(encoded)) + encoded
            except UnicodeEncodeError:
                raise EncodeError("String contains invalid UTF-8")

        elif isinstance(value, bytes):
            if len(value) > MAX_STR_SIZE:
                raise EncodeError(f"Bytes too large: {len(value)}")
            return TYPE_MARKERS[TYPE_BYTES] + self._encode_size(len(value)) + value

        elif isinstance(value, list):
            return self._encode_container(value, depth, TYPE_LIST)

        elif isinstance(value, dict):
            return self._encode_container(value, depth, TYPE_DICT)

        else:
            raise EncodeError(f"Unsupported type: {type(value)}")

    def _decode_value_impl(  # noqa: C901
        self, encoded: BinaryCodecEncodedValue, depth: int
    ) -> BinaryCodecValue:
        if not isinstance(encoded, bytes):
            raise DecodeError(f"Expected bytes, got {type(encoded)}")

        if not encoded:
            return None

        type_marker = encoded[0]
        data = encoded[1:]

        if type_marker == TYPE_NONE:
            if data:
                raise DecodeError("Extra data after None")
            return None

        if type_marker == TYPE_TRUE:
            if data:
                raise DecodeError("Extra data after True")
            return True

        if type_marker == TYPE_FALSE:
            if data:
                raise DecodeError("Extra data after False")
            return False

        if type_marker == TYPE_INT:
            if len(data) != 8:
                raise DecodeError("Invalid integer size")
            try:
                return INT64_STRUCT.unpack(data)[0]
            except struct.error:
                raise DecodeError("Failed to decode integer")

        if type_marker == TYPE_FLOAT:
            if len(data) != 8:
                raise DecodeError("Invalid float size")
            try:
                return DOUBLE_STRUCT.unpack(data)[0]
            except struct.error:
                raise DecodeError("Failed to decode float")

        if type_marker == TYPE_STR:
            state = DecoderState(data)
            size = self._decode_size(state)
            if size > MAX_STR_SIZE:
                raise DecodeError(f"String too large: {size} bytes")

            str_data = data[state.offset : state.offset + size]
            if len(str_data) != size:
                raise DecodeError("String data truncated")

            try:
                return str_data.decode("utf-8")
            except UnicodeDecodeError:
                raise DecodeError("Invalid UTF-8 in string")

        if type_marker == TYPE_BYTES:
            state = DecoderState(data)
            size = self._decode_size(state)
            if size > MAX_STR_SIZE:
                raise DecodeError(f"Bytes too large: {size}")

            bytes_data = data[state.offset : state.offset + size]
            if len(bytes_data) != size:
                raise DecodeError("Bytes data truncated")
            return bytes_data

        if type_marker == TYPE_LIST:
            state = DecoderState(data, depth=depth)
            return self._decode_container(state, is_list=True)

        if type_marker == TYPE_DICT:
            state = DecoderState(data, depth=depth)
            return self._decode_container(state, is_list=False)

        raise DecodeError(f"Unknown type marker: {type_marker}")

    def _decode_size(self, state: DecoderState) -> int:
        """Decode size value from current position."""
        if state.offset + 4 > len(state.data):
            raise DecodeError("Truncated size field")

        try:
            size = UINT32_STRUCT.unpack(state.data[state.offset : state.offset + 4])[0]
            state.offset += 4
            return size
        except struct.error:
            raise DecodeError("Invalid size field")

    def _decode_container(self, state: DecoderState, is_list: bool) -> list[Any] | dict[str, Any]:
        """Decode list or dict from current position."""
        if state.depth >= MAX_DEPTH:
            raise DecodeError(f"Maximum nesting depth ({MAX_DEPTH}) exceeded")

        result: list[BinaryCodecValue] | dict[str, BinaryCodecValue] = [] if is_list else {}
        count = 0

        while state.offset < len(state.data):
            if state.data[state.offset : state.offset + 1] == TYPE_MARKERS[TYPE_END]:
                state.offset += 1
                return result

            if count >= MAX_COLLECTION_SIZE:
                raise DecodeError(f"Collection too large: {count} items")

            if is_list:
                size = self._decode_size(state)
                if state.offset + size > len(state.data):
                    raise DecodeError("List item truncated")

                value = self._decode_value_impl(
                    state.data[state.offset : state.offset + size], state.depth + 1
                )
                result.append(value)  # type: ignore
                state.offset += size

            else:  # dict
                # Decode key
                key_size = self._decode_size(state)
                if state.offset + key_size > len(state.data):
                    raise DecodeError("Dict key truncated")

                key = self._decode_value_impl(
                    state.data[state.offset : state.offset + key_size], state.depth + 1
                )
                if not isinstance(key, str):
                    raise DecodeError(f"Dict keys must be strings, got {type(key)}")
                state.offset += key_size

                # Decode value
                val_size = self._decode_size(state)
                if state.offset + val_size > len(state.data):
                    raise DecodeError("Dict value truncated")

                value = self._decode_value_impl(
                    state.data[state.offset : state.offset + val_size], state.depth + 1
                )
                result[key] = value  # type: ignore
                state.offset += val_size

            count += 1

        raise DecodeError("Unterminated container")
