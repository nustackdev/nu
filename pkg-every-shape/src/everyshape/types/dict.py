"""Dict type — mutable mapping.

DictBase         = MutableMappingBase (dict IS mutable)
ReactiveDictBase = DictBase + ViewObservable
"""

from __future__ import annotations

from everyshape.collections import MutableMappingBase, ReactiveMappingBase


__all__ = [
    "DictBase",
    "ReactiveDictBase",
]


class DictBase[K, V](
    MutableMappingBase[K, V, object, object],
):
    """Dict — mutable mapping."""


class ReactiveDictBase[K, V](
    ReactiveMappingBase[K, V, object, object],
    DictBase[K, V],
):
    """Reactive dict — mutable + observable."""
