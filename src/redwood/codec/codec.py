"""Storage codec implementation combining key and value codecs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from mesh import ResourceSpec, SyncResource


if TYPE_CHECKING:
    from redwood.abc import TupleKey, Value
    from redwood.backends import KeyCodecProtocol, StorageCodecProtocol, ValueCodecProtocol

__all__ = [
    "StorageCodec",
    "StorageCodecSpec",
]


class StorageCodec[EncodedKeyT, EncodedValueT](SyncResource):
    """Unified codec for storage operations.

    Combines separate key and value codecs into a single interface for
    storage engines. This allows different serialization strategies for
    keys (which may need lexicographic ordering) and values (which may
    prioritize compactness or compatibility).

    Attributes:
        key_codec: Codec instance for key encoding/decoding
        value_codec: Codec instance for value encoding/decoding
        encode_key: Direct function reference for key encoding (zero overhead)
        decode_key: Direct function reference for key decoding (zero overhead)
        encode_value: Direct function reference for value encoding (zero overhead)
        decode_value: Direct function reference for value decoding (zero overhead)

    Performance:
        All encode/decode operations are direct function references to avoid
        method call overhead and maintain maximum throughput.
    """

    spec: StorageCodecSpec[EncodedKeyT, EncodedValueT]  # type: ignore[override]

    key_codec: KeyCodecProtocol[EncodedKeyT]
    value_codec: ValueCodecProtocol[EncodedValueT]

    def setup(self) -> None:
        """Initialize storage codec with key and value codec instances.

        Creates codec instances from the specification and sets up direct
        function references for all encode/decode operations.
        """
        self.key_codec = self.spec.key_codec()
        self.value_codec = self.spec.value_codec()

        self.encode_key = self.key_codec.encode
        self.decode_key = self.key_codec.decode
        self.encode_value = self.value_codec.encode
        self.decode_value = self.value_codec.decode

    def encode_key(self, key: TupleKey) -> EncodedKeyT:
        """Encode a key using the key codec."""
        raise NotImplementedError

    def decode_key(self, encoded: EncodedKeyT) -> TupleKey:
        """Decode a key using the key codec."""
        raise NotImplementedError

    def encode_value(self, value: Value) -> EncodedValueT:
        """Encode a value using the value codec."""
        raise NotImplementedError

    def decode_value(self, encoded: EncodedValueT) -> Value:
        """Decode a value using the value codec."""
        raise NotImplementedError


@attrs.define(frozen=True, slots=True, kw_only=True)
class StorageCodecSpec[EncodedKeyT, EncodedValueT](ResourceSpec):
    """Specification for StorageCodec resource.

    Attributes:
        name: Resource name
        factory: StorageCodec class
        key_codec: Key codec factory (callable returning a codec instance)
        value_codec: Value codec factory (callable returning a codec instance)
    """

    name: str = "storage_codec"
    factory: type[StorageCodec[EncodedKeyT, EncodedValueT]] = StorageCodec
    key_codec: type[KeyCodecProtocol[EncodedKeyT]]
    value_codec: type[ValueCodecProtocol[EncodedValueT]]


if TYPE_CHECKING:
    _: type[StorageCodecProtocol] = StorageCodec
