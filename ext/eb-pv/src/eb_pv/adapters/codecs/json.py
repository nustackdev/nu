"""Codec adapter."""

from __future__ import annotations


try:
    from virtuals.codecs.json import JSONCodec
except ImportError as e:
    raise ImportError("dependency missing for tkv (pip install tkv)") from e


__all__ = [
    "JSONCodec",
]
