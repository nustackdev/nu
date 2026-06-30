"""Collection interfaces."""

from . import abc
from .dict_ import DictForm
from .iterator_ import IteratorForm
from .list_ import ListForm
from .set_ import FrozenSetForm, SetForm
from .tuple_ import TupleForm
from .views import DictItemsForm, DictKeysForm, DictValuesForm


__all__ = [
    "DictForm",
    "DictItemsForm",
    "DictKeysForm",
    "DictValuesForm",
    "FrozenSetForm",
    "IteratorForm",
    "ListForm",
    "SetForm",
    "TupleForm",
]
