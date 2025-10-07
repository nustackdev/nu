from __future__ import annotations

import pickle  # nosec: b403

import attrs
from mesh import ResourceSpec, SyncResource


__all__ = [
    "PickleCodec",
    "PickleCodecSpec",
]


class PickleCodec(SyncResource):
    def setup(self) -> None:
        self.encode = pickle.dumps
        self.decode = pickle.loads


@attrs.define(frozen=True, slots=True, kw_only=True)
class PickleCodecSpec(ResourceSpec):
    name: str = "pickle_codec"
    factory: type = PickleCodec
