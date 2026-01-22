"""Codec adapters.

Individual codecs can be imported from their respective modules:
    from every_adapters.codecs.json import JSONCodec
    from every_adapters.codecs.msgpack import MessagePackCodec
    from every_adapters.codecs.micropack import MicroPackCodec
    from every_adapters.codecs.pickle import PickleCodec
    from every_adapters.codecs.passthrough import PassthroughCodec

Composite codecs (BinaryCodec, TextCodec, NoOpCodec) are available from this module:
    from every_adapters.codecs import BinaryCodec, TextCodec, NoOpCodec
"""

from __future__ import annotations

from functools import partial

from pv.storage import Codec

from .json import JSONCodec
from .passthrough import PassthroughCodec
from .pickle import PickleCodec  # nosec: B403


try:
    from evkv.tupkey import BinaryKeyCodec, StringKeyCodec
except ImportError as e:
    raise ImportError(
        "evkv package is required for key codecs. Install via: pip install evkv"
    ) from e


__all__ = [
    "BinaryCodec",
    "BinaryKeyCodec",
    "NoOpCodec",
    "StringKeyCodec",
    "TextCodec",
]

# =========================================================
# Composite codec factories
# =========================================================


# MicroPack-based binary codec
BinaryCodec = partial(
    Codec,
    key_codec_cls=BinaryKeyCodec,
    value_codec_cls=PickleCodec,
)

# JSON-based text codec
TextCodec = partial(
    Codec,
    key_codec_cls=StringKeyCodec,
    value_codec_cls=JSONCodec,
)

# No-op codec
NoOpCodec = partial(
    Codec,
    key_codec_cls=StringKeyCodec,
    value_codec_cls=PassthroughCodec,
)
