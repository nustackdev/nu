"""Dict type — mutable mapping.

DictType         = MutableMappingBase (dict IS mutable)
ReactiveDictType = DictType + ViewObservable
"""

from __future__ import annotations

from everybase.abc import Object
from everybase.shape.collections import MutableMappingBase, ReactiveMappingBase


__all__ = [
    "DictType",
    "ReactiveDictType",
]


class DictType[K, V](
    MutableMappingBase[K, V, object, object],
    Object[dict],
):
    """Dict — mutable mapping."""


class ReactiveDictType[K, V](
    DictType[K, V],
    ReactiveMappingBase[K, V, object, object],
    Object[dict],
):
    """Reactive dict — mutable + observable."""
