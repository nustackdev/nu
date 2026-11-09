"""Dict row: a slot holding a ``dict``, with the whole built-in surface.

Each tier is the ABC ordered-mapping tier of the same capability plus ``Dict``,
so a dict slot reads, writes and descends like any ordered mapping and also
carries what only ``dict`` has (``copy``, ``merge``, ``merge_update``). The
capability is the slot's: at the read tier the value still has its in-place
mapping calls, only ``set`` / ``erase`` on the slot are missing.

Refs put the ABC ref first, so descent (``ref[key]``) and the address chain
come before the value form, and a merged or copied dict carries the declared
types on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.forms import Dict

from ..collection import holding
from .abc.mapping import (
    MutableOrderedMappingForm,
    MutableOrderedMappingRef,
    OrderedMappingForm,
    OrderedMappingRef,
    ReactiveOrderedMappingForm,
    ReactiveOrderedMappingRef,
)


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = [
    "MutablePyDictForm",
    "MutablePyDictRef",
    "PyDictForm",
    "PyDictRef",
    "ReactivePyDictForm",
    "ReactivePyDictRef",
]


K = TypeVar("K")
V = TypeVar("V")


class PyDictForm(OrderedMappingForm, Dict[K, V]):
    """Read tier of a dict slot: the ordered mapping surface plus the dict-only calls."""

    def _wrap_mapping_result(self, operand: Nu) -> Dict[K, V]:
        declared = self._declared
        return holding(Dict(operand), dict, key=declared.key, elem=declared.elem)


class MutablePyDictForm(MutableOrderedMappingForm, PyDictForm[K, V]):
    """Mutable tier of a dict slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyDictForm(ReactiveOrderedMappingForm, MutablePyDictForm[K, V]):
    """Reactive tier of a dict slot: adds ``on_change`` and the tree-aware watches."""


# On the refs ``ref[key]`` is descent to the child ref, which replaces ``Dict``'s
# value read by design; typing cannot say the child is also the value form.


class PyDictRef(OrderedMappingRef, PyDictForm[K, V]):  # type: ignore[misc]
    """Dict slot ref, read tier: ``ref[key]`` descends to the value's child ref."""


class MutablePyDictRef(  # type: ignore[misc]
    MutableOrderedMappingRef, MutablePyDictForm[K, V], PyDictRef[K, V]
):
    """Dict slot ref, mutable tier."""


class ReactivePyDictRef(  # type: ignore[misc]
    ReactiveOrderedMappingRef, ReactivePyDictForm[K, V], MutablePyDictRef[K, V]
):
    """Dict slot ref, reactive tier."""
