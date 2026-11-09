"""List row: a slot holding a ``list``, with the whole built-in surface.

Each tier is the ABC sequence tier of the same capability plus ``List``, so a
list slot reads, writes and descends like any sequence and also carries what
only ``list`` has (``sort``, ``copy``, ``+``, ``*``, ordering comparisons). The
capability is the slot's: at the read tier the value still has its in-place
sequence calls, only ``set`` / ``erase`` on the slot are missing.

Refs put the ABC ref first, so descent (``ref[i]``) and the address chain come
before the value form.
"""

from __future__ import annotations

from typing import TypeVar

from nu.forms import List

from .abc.sequence import (
    MutableSequenceForm,
    MutableSequenceRef,
    ReactiveSequenceForm,
    ReactiveSequenceRef,
    SequenceForm,
    SequenceRef,
)


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


class MutablePyListForm(MutableSequenceForm, PyListForm[T]):
    """Mutable tier of a list slot: adds ``set``, ``erase`` and ``init``."""


class ReactivePyListForm(ReactiveSequenceForm, MutablePyListForm[T]):
    """Reactive tier of a list slot: adds ``on_change`` and the tree-aware watches."""


class PyListRef(SequenceRef, PyListForm[T]):
    """List slot ref, read tier: ``ref[i]`` descends to the element's child ref."""


class MutablePyListRef(MutableSequenceRef, MutablePyListForm[T], PyListRef[T]):
    """List slot ref, mutable tier."""


class ReactivePyListRef(ReactiveSequenceRef, ReactivePyListForm[T], MutablePyListRef[T]):
    """List slot ref, reactive tier."""
