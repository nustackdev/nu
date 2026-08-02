"""``Codec``: Nu fabric wrapping a virtuals codec.

Codecs are stateless immutables - key + value serialization pair. Instances
are cheap to construct, no setup or teardown needed. That makes ``Codec`` a
bare ``Fabric`` (not ``FabricLifecycle``) - the constructor does all the
work; ``Provide`` binds the instance on ctx and inner Storage / Observer
fabrics read it via ``ctx.get(Codec)``.

Preset kwargs helpers are provided for the four common combos - binary
(pickle), text (JSON), msgpack, and noop (passthrough). They return a plain
``dict`` you can splat into ``Provide``::

    Provide(Codec, binary_kwargs(),
        Provide(RocksDBStorage, {"path": "/data"}, body),
    )
"""

from __future__ import annotations

from virtuals.tkv.codec.codec import Codec as _Codec


__all__ = [
    "Codec",
    "binary_kwargs",
    "msgpack_kwargs",
    "noop_kwargs",
    "text_kwargs",
]


class Codec(_Codec):
    """Nu-fabric codec.

    Same as ``virtuals.tkv.codec.Codec`` with an explicit constructor for
    use with ``Provide``.
    """

    def __init__(self, key_codec_cls: type, value_codec_cls: type) -> None:
        super().__init__(key_codec_cls, value_codec_cls)


def binary_kwargs() -> dict[str, type]:
    """BinaryKeyCodec + PickleCodec. Binary keys, pickled values."""
    from virtuals_binary_codec import BinaryKeyCodec

    from virtuals.codecs.pickle import PickleCodec

    return {"key_codec_cls": BinaryKeyCodec, "value_codec_cls": PickleCodec}


def noop_kwargs() -> dict[str, type]:
    """BinaryKeyCodec + PassthroughCodec. No value serialization."""
    from virtuals_binary_codec import BinaryKeyCodec

    from virtuals.codecs.passthrough import PassthroughCodec

    return {"key_codec_cls": BinaryKeyCodec, "value_codec_cls": PassthroughCodec}


def text_kwargs() -> dict[str, type]:
    """StringKeyCodec + JSONCodec. Human-readable keys and values."""
    from virtuals._backends.key_codecs import StringKeyCodec
    from virtuals.codecs.json import JSONCodec

    return {"key_codec_cls": StringKeyCodec, "value_codec_cls": JSONCodec}


def msgpack_kwargs() -> dict[str, type]:
    """BinaryKeyCodec + MessagePackCodec. Compact binary serialization."""
    from virtuals_binary_codec import BinaryKeyCodec

    from virtuals.codecs.msgpack import MessagePackCodec

    return {"key_codec_cls": BinaryKeyCodec, "value_codec_cls": MessagePackCodec}
