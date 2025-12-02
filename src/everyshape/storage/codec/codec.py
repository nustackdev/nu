"""Storage codec implementation combining key and value codecs."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyshape.loc import key
    from everyshape.types import Value

    from .protocol import CodecProtocol, KeyCodecProtocol, ValueCodecProtocol

__all__ = [
    "Codec",
]


class Codec[EncodedKeyT, EncodedValueT]:
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

    def __init__(
        self, key_codec_cls: type[KeyCodecProtocol], value_codec_cls: type[ValueCodecProtocol]
    ) -> None:
        """Initialize storage codec with key and value codec instances.

        Creates codec instances from the specification and sets up direct
        function references for all encode/decode operations.

        Args:
            key_codec_cls: Key codec cls
            value_codec_cls: Value codec cls
        """
        self.key_codec = key_codec_cls()
        self.value_codec = value_codec_cls()

        self.encode_key = self.key_codec.encode
        self.decode_key = self.key_codec.decode
        self.encode_value = self.value_codec.encode
        self.decode_value = self.value_codec.decode

    def encode_key(self, key: key.Key) -> EncodedKeyT:
        """Encode a key using the key codec."""
        raise NotImplementedError

    def decode_key(self, encoded: EncodedKeyT) -> key.Key:
        """Decode a key using the key codec."""
        raise NotImplementedError

    def encode_value(self, value: Value) -> EncodedValueT:
        """Encode a value using the value codec."""
        raise NotImplementedError

    def decode_value(self, encoded: EncodedValueT) -> Value:
        """Decode a value using the value codec."""
        raise NotImplementedError


if TYPE_CHECKING:
    _: type[CodecProtocol] = Codec
