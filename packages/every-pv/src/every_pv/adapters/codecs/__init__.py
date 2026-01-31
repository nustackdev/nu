"""Codec adapters.

Individual codecs can be imported from their respective modules:
    from every_pv.adapters.codecs.json import JSONCodec
    from every_pv.adapters.codecs.msgpack import MessagePackCodec
    from every_pv.adapters.codecs.pickle import PickleCodec
    from every_pv.adapters.codecs.passthrough import PassthroughCodec

Composite codecs (BinaryCodec, TextCodec, NoOpCodec) are available from this module:
    from every_pv.adapters.codecs import BinaryCodec, TextCodec, NoOpCodec
"""

from __future__ import annotations


try:
    from tkv.codecs import BinaryCodec, NoOpCodec, TextCodec
except ImportError as e:
    raise ImportError("tkv package is required for key codecs. Install via: pip install tkv") from e


__all__ = [
    "BinaryCodec",
    "NoOpCodec",
    "TextCodec",
]
