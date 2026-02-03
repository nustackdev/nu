"""Sequence ref hierarchy — sequence bases + Ref navigation.

SequenceRefBase         = SequenceBase + Ref
MutableSequenceRefBase  = MutableSequenceBase + SequenceRefBase
ReactiveSequenceRefBase = ReactiveSequenceBase + MutableSequenceRefBase
"""

from __future__ import annotations

from ..collections import MutableSequenceBase, ReactiveSequenceBase, SequenceBase
from .base import Ref


__all__ = [
    "MutableSequenceRefBase",
    "ReactiveSequenceRefBase",
    "SequenceRefBase",
]


class SequenceRefBase[T, CollectionValueT, ItemValueT](
    SequenceBase[T, CollectionValueT, ItemValueT],
    Ref[list[T]],
):
    """Sequence ref — ordered container with document-model navigation."""


class MutableSequenceRefBase[T, CollectionValueT, ItemValueT](
    MutableSequenceBase[T, CollectionValueT, ItemValueT],
    SequenceRefBase[T, CollectionValueT, ItemValueT],
):
    """Mutable sequence ref — mutations + navigation."""


class ReactiveSequenceRefBase[T, CollectionValueT, ItemValueT](
    ReactiveSequenceBase[T, CollectionValueT, ItemValueT],
    MutableSequenceRefBase[T, CollectionValueT, ItemValueT],
):
    """Reactive sequence ref — observation + mutations + navigation."""
