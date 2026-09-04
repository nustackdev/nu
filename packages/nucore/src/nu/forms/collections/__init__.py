"""Collection interfaces."""

from . import abc
from .dict_ import Dict
from .iterator_ import Iterator
from .list_ import List
from .set_ import FrozenSet, Set
from .tuple_ import Tuple
from .views import DictItems, DictKeys, DictValues


__all__ = [
    "Dict",
    "DictItems",
    "DictKeys",
    "DictValues",
    "FrozenSet",
    "Iterator",
    "List",
    "Set",
    "Tuple",
    "abc",
]
