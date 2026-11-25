"""Collection interfaces."""

from . import abc
from .dict_ import DictSurface
from .iterator_ import IteratorSurface
from .list_ import ListSurface
from .set_ import FrozenSetSurface, SetSurface
from .tuple_ import TupleSurface
from .views import (
    DictItemsSurface,
    DictKeysSurface,
    DictValuesSurface,
)


__all__ = [
    "DictItemsSurface",
    "DictKeysSurface",
    "DictSurface",
    "DictValuesSurface",
    "FrozenSetSurface",
    "IteratorSurface",
    "ListSurface",
    "SetSurface",
    "TupleSurface",
    "abc",
]
