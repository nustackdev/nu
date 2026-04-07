"""Shaped DictI - the complete document-model dict.

Mutable, reactive, collection-aware. Just like Python says dict is a
MutableMapping, we say shaped DictI is a reactive mutable mapping with
collection ops.
"""

from __future__ import annotations

from nu.interface import Interface

from .abc import ReactiveMappingI


__all__ = [
    "DictI",
]


class DictI[K, V](
    ReactiveMappingI[K, V, object, object],
    Interface[dict],
):
    """Shaped dict - reactive mutable mapping with collection ops."""
