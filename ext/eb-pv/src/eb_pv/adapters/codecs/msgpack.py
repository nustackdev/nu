"""Codec adapter."""

from __future__ import annotations


try:
    from virtuals.codecs.msgpack import MessagePackCodec
except ImportError as e:
    raise ImportError("dependency missing for tkv (pip install tkv)") from e


__all__ = [
    "MessagePackCodec",
]
