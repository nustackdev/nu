import attrs
from mesh import ResourceSpec, SyncResource


class StorageCodec(SyncResource):
    def setup(self):
        self.key_codec = self.spec.key_codec()
        self.value_codec = self.spec.value_codec()

        self.encode_key = self.key_codec.encode
        self.decode_key = self.key_codec.decode
        self.encode_value = self.value_codec.encode
        self.decode_value = self.value_codec.decode


@attrs.frozen(slots=True, kw_only=True)
class StorageCodecSpec(ResourceSpec):
    name: str = "storage_codec"
    factory: type = StorageCodec
    key_codec: type
    value_codec: type
