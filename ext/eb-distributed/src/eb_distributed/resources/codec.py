"""CodecResource - composables Resource wrapping a virtuals Codec.

Configurable key and value codec classes. All codec combinations
from virtuals are supported via spec parameters:

Key codecs: BinaryKeyCodec, PyBinaryKeyCodec, StringKeyCodec
Value codecs: JSONCodec, MessagePackCodec, PickleCodec, PassthroughCodec
"""

from __future__ import annotations

import attrs
from composables import Resource, ResourceSpec
from virtuals.tkv.codec.codec import Codec


__all__ = [
    "CodecResource",
    "CodecSpec",
    "binary_codec_spec",
    "msgpack_codec_spec",
    "noop_codec_spec",
    "text_codec_spec",
]


class CodecResource(Resource, Codec):
    """Resource that IS a Codec."""

    spec: CodecSpec

    def __init__(self, spec: object = None, /) -> None:
        Resource.__init__(self, spec)

    async def setup(self) -> None:
        """Init Codec from spec's key/value codec classes."""
        Codec.__init__(self, self.spec.key_codec_cls, self.spec.value_codec_cls)


@attrs.define(frozen=True, slots=True, kw_only=True)
class CodecSpec(ResourceSpec):
    """Spec for CodecResource."""

    factory: type = CodecResource
    name: str = "codec"

    key_codec_cls: type = attrs.field()
    value_codec_cls: type = attrs.field()

    @key_codec_cls.default
    def _default_key_codec(self) -> type:
        from virtuals._backends.key_codecs import StringKeyCodec

        return StringKeyCodec

    @value_codec_cls.default
    def _default_value_codec(self) -> type:
        from virtuals.codecs.passthrough import PassthroughCodec

        return PassthroughCodec


# ============================================================================
# Convenience factories for common codec combinations
# ============================================================================


def noop_codec_spec() -> CodecSpec:
    """BinaryKeyCodec + PassthroughCodec. No value serialization."""
    from virtuals.codecs.passthrough import PassthroughCodec
    from virtuals_binary_codec import BinaryKeyCodec

    return CodecSpec(key_codec_cls=BinaryKeyCodec, value_codec_cls=PassthroughCodec)


def binary_codec_spec() -> CodecSpec:
    """BinaryKeyCodec + PickleCodec. Binary keys, pickled values."""
    from virtuals.codecs.pickle import PickleCodec
    from virtuals_binary_codec import BinaryKeyCodec

    return CodecSpec(key_codec_cls=BinaryKeyCodec, value_codec_cls=PickleCodec)


def text_codec_spec() -> CodecSpec:
    """StringKeyCodec + JSONCodec. Human-readable keys and values."""
    from virtuals._backends.key_codecs import StringKeyCodec
    from virtuals.codecs.json import JSONCodec

    return CodecSpec(key_codec_cls=StringKeyCodec, value_codec_cls=JSONCodec)


def msgpack_codec_spec() -> CodecSpec:
    """BinaryKeyCodec + MessagePackCodec. Compact binary serialization."""
    from virtuals.codecs.msgpack import MessagePackCodec
    from virtuals_binary_codec import BinaryKeyCodec

    return CodecSpec(key_codec_cls=BinaryKeyCodec, value_codec_cls=MessagePackCodec)
