"""List row: a slot holding a ``list``, with the whole built-in surface.

Each tier is the ABC sequence tier of the same capability plus ``List``, so a
list slot reads, writes and descends like any sequence and also carries what
only ``list`` has (``sort``, ``copy``, ``+``, ``*``, ordering comparisons). The
capability is the slot's: at the read tier the value still has its in-place
sequence calls, only ``set`` / ``erase`` on the slot are missing.

Refs put the ABC ref first, so descent (``ref[i]``) and the address chain come
before the value form. A slice reads as a ``List`` carrying the declared element
type on.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from nu.forms import List

from ..collection import holding
from .abc.sequence import (
    MutableSequenceForm,
    MutableSequenceRef,
    ReactiveSequenceForm,
    ReactiveSequenceRef,
    SequenceForm,
    SequenceRef,
)


if TYPE_CHECKING:
    from nu.lang import Nu


__all__ = [
    "MutablePyListForm",
    "MutablePyListRef",
    "PyListForm",
    "PyListRef",
    "ReactivePyListForm",
    "ReactivePyListRef",
]


T = TypeVar("T")


class PyListForm(SequenceForm, List[T]):
    """Read tier of a list slot: the sequence surface plus the list-only calls."""

    def _wrap_sliceable_result(self, operand: Nu) -> List[T]:
        return holding(List(operand), list, elem=self._declared.elem)


class MutablePyListForm(MutableSequenceForm, PyListForm[T]):
    """Mutable tier of a list slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyListForm(ReactiveSequenceForm, MutablePyListForm[T]):
    """Reactive tier of a list slot: adds ``on_change`` and the tree-aware watches."""


# On the refs ``ref[i]`` is descent to the child ref, which replaces ``List``'s
# element read by design; typing cannot say the child is also the element form.


class PyListRef(SequenceRef, PyListForm[T]):  # type: ignore[misc]
    """List slot ref, read tier: ``ref[i]`` descends to the element's child ref."""


class MutablePyListRef(MutableSequenceRef, MutablePyListForm[T], PyListRef[T]):  # type: ignore[misc]
    """List slot ref, mutable tier."""


class ReactivePyListRef(  # type: ignore[misc]
    ReactiveSequenceRef, ReactivePyListForm[T], MutablePyListRef[T]
):
    """List slot ref, reactive tier."""
