from loomi.service import SyncService

from .types import (
    PassthroughCodecEncodedKey,
    PassthroughCodecEncodedValue,
    PassthroughCodecKey,
    PassthroughCodecValue,
)

__all__ = ["PassthroughCodec"]

class PassthroughCodec(SyncService):
    def encode_key(self, key: PassthroughCodecKey) -> PassthroughCodecEncodedKey: ...
    def decode_key(self, encoded: PassthroughCodecEncodedKey) -> PassthroughCodecKey: ...
    def encode_value(self, value: PassthroughCodecValue) -> PassthroughCodecEncodedValue: ...
    def decode_value(self, encoded: PassthroughCodecEncodedValue) -> PassthroughCodecValue: ...
