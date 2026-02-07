"""Dict type — mutable mapping.

DictType         = MutableMappingBase (dict IS mutable)
ReactiveDictType = DictType + ViewObservable
"""

from __future__ import annotations

from eb_shape.collections import MutableMappingBase, ReactiveMappingBase
from everybase.abc import TypeBase


__all__ = [
    "DictType",
    "ReactiveDictType",
]


class DictType[K, V](
    MutableMappingBase[K, V, object, object],
    TypeBase[dict],
):
    """Dict — mutable mapping."""


class ReactiveDictType[K, V](
    DictType[K, V],
    ReactiveMappingBase[K, V, object, object],
    TypeBase[dict],
):
    """Reactive dict — mutable + observable."""
