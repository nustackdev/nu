"""Nu shape domain: declare structure once, reach it through refs any fabric backs.

A Shape declares slots; each slot is a ref blueprint that a fabric completes
with its own storage. Blueprints come in families (item, mapping, sequence,
set, shape), each in three tiers (read, mutable, reactive), and carry the whole
Form surface of their family. A fabric supplies only how a path is read and
written, and which of its refs a descent lands on.

Reactive queries (``OnChange`` and its tree-aware siblings) live in
``nu.core.reactive``, one interface for every substrate, reached through the
shape Form mixins.
"""

from __future__ import annotations

from .base import StructuredRef, root_shape
from .collection import ReactiveCollectionForm, holding
from .dsl import Shape, ShapeMeta, Slot, SlotDescriptor
from .interactions import (
    AdvanceCursor,
    Erase,
    Exists,
    Extract,
    Load,
    PrimitiveSet,
    SetCmd,
)
from .item import ItemRef, MutableItemRef, ReactiveItemRef
from .mapping import (
    MappingRef,
    MutableMappingRef,
    MutableOrderedMappingRef,
    OrderedMappingRef,
    ReactiveMappingRef,
    ReactiveOrderedMappingRef,
)
from .rewrite import reroot, rerooter, with_parent
from .sequence import MutableSequenceRef, ReactiveSequenceRef, SequenceRef
from .set_ import MutableSetRef, ReactiveSetRef, SetRef
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "AdvanceCursor",
    "Erase",
    "Exists",
    "Extract",
    "ItemRef",
    "Load",
    "MappingRef",
    "MutableItemRef",
    "MutableMappingRef",
    "MutableOrderedMappingRef",
    "MutableSequenceRef",
    "MutableSetRef",
    "MutableShapeRef",
    "OrderedMappingRef",
    "PrimitiveSet",
    "ReactiveCollectionForm",
    "ReactiveItemRef",
    "ReactiveMappingRef",
    "ReactiveOrderedMappingRef",
    "ReactiveSequenceRef",
    "ReactiveSetRef",
    "ReactiveShapeRef",
    "SequenceRef",
    "SetCmd",
    "SetRef",
    "Shape",
    "ShapeMeta",
    "ShapeRef",
    "Slot",
    "SlotDescriptor",
    "StructuredRef",
    "holding",
    "reroot",
    "rerooter",
    "root_shape",
    "with_parent",
]
