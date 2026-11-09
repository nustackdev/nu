"""Nu shape domain: declare structure once, reach it through refs any fabric backs.

A Shape declares slots; each slot is a ref blueprint that a fabric completes
with its own storage. A fabric supplies only how a path is read and written,
and which of its refs a descent lands on.

The blueprints form a grid laid out like ``nu.forms``. Every ``nu.forms`` type
has a row, and a row is named after its form: ``Form`` swapped for ``Ref``.

- ABC rows (``collections/abc``): one ref per ABC tier, with the slot's
  capability growing with the tier: ``MappingRef``, ``MutableMappingRef``,
  ``ReactiveMappingRef``; ``OrderedMappingRef`` and its tiers;
  ``SequenceRef`` and its tiers; ``SetLikeRef`` and ``MutableSetRef``.
- Built-in rows (``collections``: dict, list, set, frozenset, tuple) and
  primitive rows (``primitives``: int, str, float, bool, bytes, object): two
  refs each. The base ref (``DictRef``, ``IntRef``...) carries the slot
  capability (exists, extract, set, erase, init); the reactive ref
  (``ReactiveDictRef``, ``ReactiveIntRef``...) adds the watches.

Each ref is composed directly: the ``nu.forms`` type, the slot capability base
and ``StructuredRef``. A fabric ref picks one and adds its fabric base; the
fabrics name theirs the same way, so they import this package qualified
(``shape.DictRef``).

Reactive queries (``OnChange`` and its tree-aware siblings) live in
``nu.core.reactive``, one interface for every substrate, reached through the
shape Form mixins.
"""

from __future__ import annotations

from .base import StructuredRef, root_shape
from .collection import MutableCollectionForm, ReactiveCollectionForm, holding
from .collections import (
    DictRef,
    FrozenSetRef,
    ListRef,
    ReactiveDictRef,
    ReactiveFrozenSetRef,
    ReactiveListRef,
    ReactiveSetRef,
    ReactiveTupleRef,
    SetRef,
    TupleRef,
)
from .collections.abc import (
    MappingRef,
    MutableMappingRef,
    MutableOrderedMappingRef,
    MutableSequenceRef,
    MutableSetRef,
    OrderedMappingRef,
    ReactiveMappingRef,
    ReactiveOrderedMappingRef,
    ReactiveSequenceRef,
    SequenceRef,
    SetLikeRef,
)
from .dsl import Shape, ShapeMeta, Slot, SlotDescriptor
from .extractable import Extractable
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
from .primitives import (
    BoolRef,
    BytesRef,
    FloatRef,
    IntRef,
    ObjectRef,
    ReactiveBoolRef,
    ReactiveBytesRef,
    ReactiveFloatRef,
    ReactiveIntRef,
    ReactiveObjectRef,
    ReactiveStrRef,
    StrRef,
)
from .rewrite import reroot, rerooter, with_parent
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "AdvanceCursor",
    "BoolRef",
    "BytesRef",
    "DictRef",
    "Erase",
    "Exists",
    "Extract",
    "Extractable",
    "FloatRef",
    "FrozenSetRef",
    "IntRef",
    "ItemRef",
    "ListRef",
    "Load",
    "MappingRef",
    "MutableCollectionForm",
    "MutableItemRef",
    "MutableMappingRef",
    "MutableOrderedMappingRef",
    "MutableSequenceRef",
    "MutableSetRef",
    "MutableShapeRef",
    "ObjectRef",
    "OrderedMappingRef",
    "PrimitiveSet",
    "ReactiveBoolRef",
    "ReactiveBytesRef",
    "ReactiveCollectionForm",
    "ReactiveDictRef",
    "ReactiveFloatRef",
    "ReactiveFrozenSetRef",
    "ReactiveIntRef",
    "ReactiveItemRef",
    "ReactiveListRef",
    "ReactiveMappingRef",
    "ReactiveObjectRef",
    "ReactiveOrderedMappingRef",
    "ReactiveSequenceRef",
    "ReactiveSetRef",
    "ReactiveShapeRef",
    "ReactiveStrRef",
    "ReactiveTupleRef",
    "SequenceRef",
    "SetCmd",
    "SetLikeRef",
    "SetRef",
    "Shape",
    "ShapeMeta",
    "ShapeRef",
    "Slot",
    "SlotDescriptor",
    "StrRef",
    "StructuredRef",
    "TupleRef",
    "holding",
    "reroot",
    "rerooter",
    "root_shape",
    "with_parent",
]
