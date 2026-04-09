"""Collection interfaces."""

from . import abc
from .dict_ import DictI
from .iterator_ import IteratorI
from .list_ import ListI
from .set_ import FrozenSetI, SetI
from .tuple_ import TupleI
from .views import DictItemsI, DictKeysI, DictValuesI


__all__ = [
    "DictI",
    "DictItemsI",
    "DictKeysI",
    "DictValuesI",
    "FrozenSetI",
    "IteratorI",
    "ListI",
    "SetI",
    "TupleI",
]
