"""Set rows: a slot holding a ``set`` or a ``frozenset``, with the whole built-in surface.

Two refs per row. ``SetRef`` is the mutable set ref plus ``Set``, so it also
carries ``copy``; ``FrozenSetRef`` is the set-like ref plus ``FrozenSet``
under the mutable slot capability: the slot can be set, erased and
initialised, but the value never changes in place, so it carries no ``add``,
``discard`` or in-place update. The reactive refs add the watches.

Set algebra reads as the row's own type (a ``Set`` or a ``FrozenSet``)
carrying the declared element type on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.forms import FrozenSet, Set

from ..collection import MutableCollectionForm, ReactiveCollectionForm, holding
from .abc.set_ import MutableSetRef, ReactiveSetForm, SetLikeRef


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = ["FrozenSetRef", "ReactiveFrozenSetRef", "ReactiveSetRef", "SetRef"]


T = TypeVar("T")


# ---- set ---------------------------------------------------------------------


class SetRef(MutableSetRef, Set[T]):
    """Set slot ref. A set has no keys, so there is no descent."""

    def _wrap_set_result(self, operand: Nu) -> Set[T]:
        return holding(Set(operand), set, elem=self._declared.elem)


class ReactiveSetRef(ReactiveSetForm, SetRef[T]):
    """Set slot ref that can be watched: adds ``on_change`` and the tree-aware watches."""


# ---- frozenset ---------------------------------------------------------------


class FrozenSetRef(MutableCollectionForm, SetLikeRef, FrozenSet[T]):
    """Frozenset slot ref. No descent."""

    def _wrap_set_result(self, operand: Nu) -> FrozenSet[T]:
        return holding(FrozenSet(operand), frozenset, elem=self._declared.elem)


class ReactiveFrozenSetRef(ReactiveCollectionForm, FrozenSetRef[T]):
    """Frozenset slot ref that can be watched: adds ``on_change`` and the tree-aware watches."""
