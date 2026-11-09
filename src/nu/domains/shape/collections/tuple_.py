"""Tuple row: a slot holding a ``tuple``. The slot is writable, the value is not.

Two refs. ``TupleRef`` is the sequence ref plus ``Tuple`` under the mutable
slot capability: the slot can be set, erased and initialised, but the tuple
never changes in place, so it carries none of the mutable sequence calls
(``append``, ``insert``, ...). ``ReactiveTupleRef`` adds the watches.

A slice reads as a ``Tuple`` carrying the declared element type on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import TypeVarTuple, Unpack

from nu.forms import Tuple

from ..collection import MutableCollectionForm, ReactiveCollectionForm, holding
from .abc.sequence import SequenceRef


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["ReactiveTupleRef", "TupleRef"]


Ts = TypeVarTuple("Ts")


class TupleRef(MutableCollectionForm, SequenceRef, Tuple[Unpack[Ts]]):
    """Tuple slot ref: ``ref[i]`` descends to the element's child ref."""

    def _wrap_sliceable_result(self, operand: Nu) -> Tuple:
        return holding(Tuple(operand), tuple, elem=self._declared.elem)


class ReactiveTupleRef(ReactiveCollectionForm, TupleRef[Unpack[Ts]]):
    """Tuple slot ref that can be watched: adds ``on_change`` and the tree-aware watches."""
