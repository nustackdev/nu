"""Shapes collections - ABCs and concrete type interfaces."""

from .abc import (
    CollectionI,
    ItemI,
    MappingI,
    MutableCollectionI,
    MutableItemI,
    MutableMappingI,
    MutableSequenceI,
    MutableSetI,
    ReactiveCollectionI,
    ReactiveItemI,
    ReactiveMappingI,
    ReactiveSequenceI,
    ReactiveSetI,
    SequenceI,
    SetLikeI,
)
from .dict import DictI
from .frozenset import FrozenSetI
from .list import ListI
from .set import SetI
from .tuple import TupleI
