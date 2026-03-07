"""Codec adapter."""

from __future__ import annotations


try:
    from virtuals.codecs.passthrough import PassthroughCodec
except ImportError as e:
    raise ImportError("dependency missing for tkv (pip install tkv)") from e


__all__ = [
    "PassthroughCodec",
]
