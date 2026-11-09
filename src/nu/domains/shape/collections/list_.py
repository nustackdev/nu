"""List row: a slot holding a ``list``, with the whole built-in surface.

Two refs. ``ListRef`` is the mutable sequence ref plus ``List``: the slot
reads, writes, descends and can be set, erased and initialised, and the value
carries what only ``list`` has (``sort``, ``copy``, ``+``, ``*``, ordering
comparisons). ``ReactiveListRef`` adds the watches.

The ABC ref comes first, so descent (``ref[i]``) and the address chain come
before the value form. A slice reads as a ``List`` carrying the declared
element type on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.forms import List

from ..collection import holding
from .abc.sequence import MutableSequenceRef, ReactiveSequenceRef


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["ListRef", "ReactiveListRef"]


T = TypeVar("T")


# On the refs ``ref[i]`` is descent to the child ref, which replaces ``List``'s
# element read by design; typing cannot say the child is also the element form.


class ListRef(MutableSequenceRef, List[T]):  # type: ignore[misc]
    """List slot ref: ``ref[i]`` descends to the element's child ref."""

    def _wrap_sliceable_result(self, operand: Nu) -> List[T]:
        return holding(List(operand), list, elem=self._declared.elem)


class ReactiveListRef(ReactiveSequenceRef, ListRef[T]):  # type: ignore[misc]
    """List slot ref that can be watched: adds ``on_change`` and the tree-aware watches."""
