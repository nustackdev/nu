"""Collection interfaces."""

from .dict_ import DictI
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
    "ListI",
    "SetI",
    "TupleI",
]
