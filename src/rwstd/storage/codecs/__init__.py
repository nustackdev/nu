"""Codec adapters."""

from __future__ import annotations

from functools import partial

from redwood.storage import Codec
from rwtup import BinaryKeyCodec, StringKeyCodec

from .json import JSONCodec
from .micropack import MicroPackCodec
from .msgpack import MessagePackCodec
from .passthrough import PassthroughCodec
from .pickle import PickleCodec


__all__ = [  # noqa: RUF022
    # Storage codecs
    "BinaryCodec",
    "NoOpCodec",
    "TextCodec",
    # Adapters for common codecs
    "JSONCodec",
    "MicroPackCodec",
    "MessagePackCodec",
    "PassthroughCodec",
    "PickleCodec",
    # Re-export rwtup key codecs
    "BinaryKeyCodec",
    "StringKeyCodec",
]

# =========================================================
# Aliases for common codec types
# =========================================================


# MicroPack-based binary codec
BinaryCodec = partial(
    Codec,
    key_codec_cls=BinaryKeyCodec,
    value_codec_cls=MicroPackCodec,
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
