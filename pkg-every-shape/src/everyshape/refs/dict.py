"""Mapping ref hierarchy — mapping bases + Ref navigation.

MappingRefBase         = MappingBase + Ref
MutableMappingRefBase  = MutableMappingBase + MappingRefBase
ReactiveMappingRefBase = ReactiveMappingBase + MutableMappingRefBase
"""

from __future__ import annotations

from ..collections import MappingBase, MutableMappingBase, ReactiveMappingBase
from .base import Ref


__all__ = [
    "MappingRefBase",
    "MutableMappingRefBase",
    "ReactiveMappingRefBase",
]


class MappingRefBase[K, V, CollectionValueT, ValueValueT](
    MappingBase[K, V, CollectionValueT, ValueValueT],
    Ref[dict[K, V]],
):
    """Mapping ref — key-value container with document-model navigation."""


class MutableMappingRefBase[K, V, CollectionValueT, ValueValueT](
    MutableMappingBase[K, V, CollectionValueT, ValueValueT],
    MappingRefBase[K, V, CollectionValueT, ValueValueT],
):
    """Mutable mapping ref — mutations + navigation."""


class ReactiveMappingRefBase[K, V, CollectionValueT, ValueValueT](
    ReactiveMappingBase[K, V, CollectionValueT, ValueValueT],
    MutableMappingRefBase[K, V, CollectionValueT, ValueValueT],
):
    """Reactive mapping ref — observation + mutations + navigation."""
