from __future__ import annotations

import struct
from typing import cast

import attrs
import msgpack

from loomi import ResourceSpec
from loomistd.service import SyncService

from .._exceptions import DecodeError, EncodeError
from .constants import MAX_STR_SIZE, PATH_SEPARATOR
from .types import (
    MsgpackCodecEncodedKey,
    MsgpackCodecEncodedValue,
    MsgpackCodecKey,
    MsgpackCodecValue,
)

__all__ = [
    "MsgpackCodec",
    "MsgpackCodecSpec",
]


class MsgpackCodec(SyncService):
    """
    Msgpack codec implementation that reuses binary codec's key encoding and uses msgpack for values.

    Features:
    - Key encoding/decoding identical to binary codec for compatibility
    - Value encoding/decoding using msgpack for efficiency and broad type support
    - Maintains lexicographical ordering for keys
    """

    def encode_key(self, key: MsgpackCodecKey) -> MsgpackCodecEncodedKey:
        """
        Encode key tuple into bytes with lexicographical ordering.

        This implementation is identical to the binary codec's key encoding
        to maintain compatibility and ordering properties.
        """
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
                parts.extend(struct.Struct(">q").pack(part))

            else:
                raise EncodeError(f"Key parts must be str or int, got {type(part)}")

            parts.extend(PATH_SEPARATOR)

        return bytes(parts[:-1])  # Remove trailing separator

    def decode_key(self, encoded: MsgpackCodecEncodedKey) -> MsgpackCodecKey:
        """
        Decode bytes back to key tuple.

        This implementation is identical to the binary codec's key decoding
        to maintain compatibility.
        """
        if not isinstance(encoded, bytes):
            raise DecodeError(f"Expected bytes, got {type(encoded)}")

        parts = encoded.split(PATH_SEPARATOR)
        result: list[str] = []

        for part in parts:
            if not part:
                continue

            # Decode as UTF-8 string
            try:
                if len(part) > MAX_STR_SIZE:
                    raise DecodeError(f"Key string too large: {len(part)} bytes")
                result.append(part.decode("utf-8"))
            except UnicodeDecodeError:
                raise DecodeError("Invalid UTF-8 in key string")

        return tuple(result)

    def encode_value(self, value: MsgpackCodecValue) -> MsgpackCodecEncodedValue:
        """
        Encode value using msgpack.

        Args:
            value: Value to encode

        Returns:
            Msgpack-encoded bytes

        Raises:
            EncodeError: If value cannot be encoded
        """
        try:
            return cast(MsgpackCodecEncodedValue, msgpack.packb(value, use_bin_type=True))
        except Exception as e:
            raise EncodeError(f"Failed to encode value with msgpack: {e}")

    def decode_value(self, encoded: MsgpackCodecEncodedValue) -> MsgpackCodecValue:
        """
        Decode value using msgpack.

        Args:
            encoded: Msgpack-encoded bytes to decode

        Returns:
            Decoded value

        Raises:
            DecodeError: If value cannot be decoded
        """
        try:
            return cast(
                MsgpackCodecValue, msgpack.unpackb(encoded, raw=False, strict_map_key=False)
            )
        except Exception as e:
            raise DecodeError(f"Failed to decode value with msgpack: {e}")


@attrs.define(frozen=True, slots=True, kw_only=True)
class MsgpackCodecSpec(ResourceSpec):
    name: str = "msgpack_codec"
    factory: type = MsgpackCodec
