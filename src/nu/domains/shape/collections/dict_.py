"""Dict row: a slot holding a ``dict``, with the whole built-in surface.

Two refs. ``DictRef`` is the mutable ordered mapping ref plus ``Dict``: the
slot reads, writes, descends and can be set, erased and initialised, and the
value carries what only ``dict`` has (``copy``, ``merge``, ``merge_update``).
``ReactiveDictRef`` adds the watches.

The ABC ref comes first, so descent (``ref[key]``) and the address chain come
before the value form, and a merged or copied dict carries the declared types
on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.forms import Dict

from ..collection import holding
from .abc.mapping import MutableOrderedMappingRef, ReactiveOrderedMappingRef


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["DictRef", "ReactiveDictRef"]


K = TypeVar("K")
V = TypeVar("V")


# On the refs ``ref[key]`` is descent to the child ref, which replaces ``Dict``'s
# value read by design; typing cannot say the child is also the value form.


class DictRef(MutableOrderedMappingRef, Dict[K, V]):  # type: ignore[misc]
    """Dict slot ref: ``ref[key]`` descends to the value's child ref."""

    def _wrap_mapping_result(self, operand: Nu) -> Dict[K, V]:
        declared = self._declared
        return holding(Dict(operand), dict, key=declared.key, elem=declared.elem)


class ReactiveDictRef(ReactiveOrderedMappingRef, DictRef[K, V]):  # type: ignore[misc]
    """Dict slot ref that can be watched: adds ``on_change`` and the tree-aware watches."""
