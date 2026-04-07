"""Shapes collection ABCs - interface hierarchies for the document model."""

from .collection import CollectionI, MutableCollectionI, ReactiveCollectionI
from .item import ItemI, MutableItemI, ReactiveItemI
from .mapping import MappingI, MutableMappingI, ReactiveMappingI
from .sequence import MutableSequenceI, ReactiveSequenceI, SequenceI
from .set import MutableSetI, ReactiveSetI, SetLikeI
