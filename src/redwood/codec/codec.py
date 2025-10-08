"""Storage codec implementation combining key and value codecs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic

import attrs
from mesh import ResourceSpec, SyncResource

from .protocols import KeyCodecProtocol, ValueCodecProtocol
from .types import EncodedKeyT, EncodedValueT, Key, SupportedValuesT


__all__ = [
    "StorageCodec",
    "StorageCodecSpec",
]


class StorageCodec(SyncResource, Generic[EncodedKeyT, SupportedValuesT, EncodedValueT]):
    """
    Unified codec for storage operations.

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

    key_codec: KeyCodecProtocol[EncodedKeyT]
    value_codec: ValueCodecProtocol[SupportedValuesT, EncodedValueT]

    encode_key: Callable[[Key], EncodedKeyT]
    decode_key: Callable[[EncodedKeyT], Key]
    encode_value: Callable[[SupportedValuesT], EncodedValueT]
    decode_value: Callable[[EncodedValueT], SupportedValuesT]

    def setup(self) -> None:
        """
        Initialize storage codec with key and value codec instances.

        Creates codec instances from the specification and sets up direct
        function references for all encode/decode operations.
        """
        self.key_codec: KeyCodecProtocol[EncodedKeyT] = self.spec.key_codec()
        self.value_codec: ValueCodecProtocol[SupportedValuesT, EncodedValueT] = (
            self.spec.value_codec()
        )

        self.encode_key: Callable[[Key], EncodedKeyT] = self.key_codec.encode
        self.decode_key: Callable[[EncodedKeyT], Key] = self.key_codec.decode
        self.encode_value: Callable[[SupportedValuesT], EncodedValueT] = self.value_codec.encode
        self.decode_value: Callable[[EncodedValueT], SupportedValuesT] = self.value_codec.decode


@attrs.define(frozen=True, slots=True, kw_only=True)
class StorageCodecSpec(ResourceSpec, Generic[EncodedKeyT, SupportedValuesT, EncodedValueT]):
    """
    Specification for StorageCodec resource.

    Attributes:
        name: Resource name
        factory: StorageCodec class
        key_codec: Key codec factory (callable returning a codec instance)
        value_codec: Value codec factory (callable returning a codec instance)
    """

    name: str = "storage_codec"
    factory: type = StorageCodec[EncodedKeyT, SupportedValuesT, EncodedValueT]
    key_codec: KeyCodecProtocol[EncodedKeyT]
    value_codec: ValueCodecProtocol[SupportedValuesT, EncodedValueT]
