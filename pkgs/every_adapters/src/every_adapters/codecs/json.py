"""Codec adapter."""

from __future__ import annotations


try:
    from tkv.codecs.json import JSONCodec
except ImportError as e:
    raise ImportError("dependency missing for tkv (pip install tkv)") from e


__all__ = [
    "JSONCodec",
]
