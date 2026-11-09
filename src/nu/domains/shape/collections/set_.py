"""Set rows: a slot holding a ``set`` or a ``frozenset``, with the whole built-in surface.

``set``: each tier is the ABC set tier of the same capability plus ``Set``, so
it also carries ``copy``. ``frozenset``: the read tier is the ABC set tier plus
``FrozenSet``, and the tiers above add only slot capability (``set`` /
``erase``, then the watches); the value never changes in place, so no tier
carries ``add``, ``discard`` or the in-place updates.

Set algebra reads as the row's own type (a ``Set`` or a ``FrozenSet``)
carrying the declared element type on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.forms import FrozenSet, Set

from ..collection import MutableCollectionForm, ReactiveCollectionForm, holding
from .abc.set_ import (
    MutableSetForm,
    MutableSetRef,
    ReactiveSetForm,
    ReactiveSetRef,
    SetLikeForm,
    SetRef,
)


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = [
    "MutablePyFrozenSetForm",
    "MutablePyFrozenSetRef",
    "MutablePySetForm",
    "MutablePySetRef",
    "PyFrozenSetForm",
    "PyFrozenSetRef",
    "PySetForm",
    "PySetRef",
    "ReactivePyFrozenSetForm",
    "ReactivePyFrozenSetRef",
    "ReactivePySetForm",
    "ReactivePySetRef",
]


T = TypeVar("T")


# ---- set ---------------------------------------------------------------------


class PySetForm(SetLikeForm, Set[T]):
    """Read tier of a set slot: the set surface plus the set-only calls."""


class MutablePySetForm(MutableSetForm, PySetForm[T]):
    """Mutable tier of a set slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePySetForm(ReactiveSetForm, MutablePySetForm[T]):
    """Reactive tier of a set slot: adds ``on_change`` and the tree-aware watches."""


class PySetRef(SetRef, PySetForm[T]):
    """Set slot ref, read tier. A set has no keys, so there is no descent."""


class MutablePySetRef(MutableSetRef, MutablePySetForm[T], PySetRef[T]):
    """Set slot ref, mutable tier."""


class ReactivePySetRef(ReactiveSetRef, ReactivePySetForm[T], MutablePySetRef[T]):
    """Set slot ref, reactive tier."""


# ---- frozenset ---------------------------------------------------------------


class PyFrozenSetForm(SetLikeForm, FrozenSet[T]):
    """Read tier of a frozenset slot: the set surface plus the frozenset-only calls."""

    def _wrap_set_result(self, operand: Nu) -> FrozenSet[T]:
        return holding(FrozenSet(operand), frozenset, elem=self._declared.elem)


class MutablePyFrozenSetForm(MutableCollectionForm, PyFrozenSetForm[T]):
    """Mutable tier of a frozenset slot: adds ``set``, ``erase`` and ``init`` on the slot."""


class ReactivePyFrozenSetForm(ReactiveCollectionForm, MutablePyFrozenSetForm[T]):
    """Reactive tier of a frozenset slot: adds ``on_change`` and the tree-aware watches."""


class PyFrozenSetRef(SetRef, PyFrozenSetForm[T]):
    """Frozenset slot ref, read tier. No descent."""


class MutablePyFrozenSetRef(MutablePyFrozenSetForm[T], PyFrozenSetRef[T]):
    """Frozenset slot ref, mutable tier."""


class ReactivePyFrozenSetRef(ReactivePyFrozenSetForm[T], MutablePyFrozenSetRef[T]):
    """Frozenset slot ref, reactive tier."""
