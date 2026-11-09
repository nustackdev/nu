"""Tuple row: a slot holding a ``tuple``. The slot is writable, the value is not.

The read tier is the ABC sequence tier plus ``Tuple``. The tiers above add only
slot capability: the mutable tier can ``set`` / ``erase`` the slot and the
reactive tier can watch it, but the tuple never changes in place, so no tier
carries the mutable sequence calls (``append``, ``insert``, ...).

A slice reads as a ``Tuple`` carrying the declared element type on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import TypeVarTuple, Unpack

from nu.forms import Tuple

from ..collection import MutableCollectionForm, ReactiveCollectionForm, holding
from .abc.sequence import SequenceForm, SequenceRef


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = [
    "MutablePyTupleForm",
    "MutablePyTupleRef",
    "PyTupleForm",
    "PyTupleRef",
    "ReactivePyTupleForm",
    "ReactivePyTupleRef",
]


Ts = TypeVarTuple("Ts")


class PyTupleForm(SequenceForm, Tuple[Unpack[Ts]]):
    """Read tier of a tuple slot: the sequence surface plus the tuple operators."""

    def _wrap_sliceable_result(self, operand: Nu) -> Tuple:
        return holding(Tuple(operand), tuple, elem=self._declared.elem)


class MutablePyTupleForm(MutableCollectionForm, PyTupleForm[Unpack[Ts]]):
    """Mutable tier of a tuple slot: adds ``set``, ``erase`` and ``init`` on the slot."""


class ReactivePyTupleForm(ReactiveCollectionForm, MutablePyTupleForm[Unpack[Ts]]):
    """Reactive tier of a tuple slot: adds ``on_change`` and the tree-aware watches."""


class PyTupleRef(SequenceRef, PyTupleForm[Unpack[Ts]]):
    """Tuple slot ref, read tier: ``ref[i]`` descends to the element's child ref."""


class MutablePyTupleRef(MutablePyTupleForm[Unpack[Ts]], PyTupleRef[Unpack[Ts]]):
    """Tuple slot ref, mutable tier."""


class ReactivePyTupleRef(ReactivePyTupleForm[Unpack[Ts]], MutablePyTupleRef[Unpack[Ts]]):
    """Tuple slot ref, reactive tier."""
