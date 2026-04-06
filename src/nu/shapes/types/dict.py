"""Dict type — mutable mapping.

DictI         = MutableMappingBase (dict IS mutable)
ReactiveDictType = DictI + ViewObservable
"""

from __future__ import annotations

from nu.interface import Interface

from ..collections import MutableMappingBase, ReactiveMappingBase


__all__ = [
    "DictType",
    "ReactiveDictType",
]


class DictType[K, V](
    MutableMappingBase[K, V, object, object],
    Interface[dict],
):
    """Dict — mutable mapping."""


class ReactiveDictType[K, V](
    DictType[K, V],
    ReactiveMappingBase[K, V, object, object],
    Interface[dict],
):
    """Reactive dict — mutable + observable."""
