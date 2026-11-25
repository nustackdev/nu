"""Collection interfaces."""

from . import abc
from .dict_ import Dict, DictSurface
from .iterator_ import Iterator, IteratorSurface
from .list_ import List, ListSurface
from .set_ import FrozenSet, FrozenSetSurface, Set, SetSurface
from .tuple_ import Tuple, TupleSurface
from .views import (
    DictItems,
    DictItemsSurface,
    DictKeys,
    DictKeysSurface,
    DictValues,
    DictValuesSurface,
)


__all__ = [
    "Dict",
    "DictItems",
    "DictItemsSurface",
    "DictKeys",
    "DictKeysSurface",
    "DictSurface",
    "DictValues",
    "DictValuesSurface",
    "FrozenSet",
    "FrozenSetSurface",
    "Iterator",
    "IteratorSurface",
    "List",
    "ListSurface",
    "Set",
    "SetSurface",
    "Tuple",
    "TupleSurface",
    "abc",
]
