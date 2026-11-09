"""Nu shape domain: declare structure once, reach it through refs any fabric backs.

A Shape declares slots; each slot is a ref blueprint that a fabric completes
with its own storage. A fabric supplies only how a path is read and written,
and which of its refs a descent lands on.

The blueprints form a grid with two axes, laid out like ``nu.forms``:

- rows, the Python type, from ``nu.forms``: the ABC rows (``collections/abc``:
  Mapping, OrderedMapping, Sequence, Set), the built-in rows
  (``collections``: dict, list, set, frozenset, tuple) and the primitive rows
  (``primitives``: int, str, float, bool, bytes, object);
- columns, the slot's capability, from the shape bases: read
  (``CollectionForm`` / ``ItemForm``: exists, extract), mutable (set, erase,
  init) and reactive (the watches).

Every cell is an explicit class: a shape form (capability base + forms type)
and its ref (that form + ``StructuredRef``). A fabric ref picks one cell and
adds its fabric base.

Naming. ABC rows keep Python's ABC names: ``MappingRef``, ``MutableMappingRef``,
``ReactiveMappingRef``, ``SequenceRef``..., ``SetRef``... (the ``SetLikeForm``
row). Built-in and primitive rows prefix the Python type with ``Py``:
``PyDictRef``, ``MutablePyDictRef``, ``ReactivePyDictRef``, ``PySetRef``...,
``PyIntRef``... The prefix keeps them apart from the ABC ``SetRef`` family
(``MutableSetRef`` names the ``collections.abc.MutableSet`` cell, not the
mutable tier of ``set``) and from the fabric refs built on them (mem and kv
each have a ``DictRef`` on a ``Py`` cell).

Reactive queries (``OnChange`` and its tree-aware siblings) live in
``nu.core.reactive``, one interface for every substrate, reached through the
shape Form mixins.
"""

from __future__ import annotations

from .base import StructuredRef, root_shape
from .collection import MutableCollectionForm, ReactiveCollectionForm, holding
from .collections import (
    MutablePyDictRef,
    MutablePyFrozenSetRef,
    MutablePyListRef,
    MutablePySetRef,
    MutablePyTupleRef,
    PyDictRef,
    PyFrozenSetRef,
    PyListRef,
    PySetRef,
    PyTupleRef,
    ReactivePyDictRef,
    ReactivePyFrozenSetRef,
    ReactivePyListRef,
    ReactivePySetRef,
    ReactivePyTupleRef,
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
    ReactiveSetRef,
    SequenceRef,
    SetRef,
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
    MutablePyBoolRef,
    MutablePyBytesRef,
    MutablePyFloatRef,
    MutablePyIntRef,
    MutablePyObjectRef,
    MutablePyStrRef,
    PyBoolRef,
    PyBytesRef,
    PyFloatRef,
    PyIntRef,
    PyObjectRef,
    PyStrRef,
    ReactivePyBoolRef,
    ReactivePyBytesRef,
    ReactivePyFloatRef,
    ReactivePyIntRef,
    ReactivePyObjectRef,
    ReactivePyStrRef,
)
from .rewrite import reroot, rerooter, with_parent
from .shape import MutableShapeRef, ReactiveShapeRef, ShapeRef


__all__ = [
    "AdvanceCursor",
    "Erase",
    "Exists",
    "Extract",
    "Extractable",
    "ItemRef",
    "Load",
    "MappingRef",
    "MutableCollectionForm",
    "MutableItemRef",
    "MutableMappingRef",
    "MutableOrderedMappingRef",
    "MutablePyBoolRef",
    "MutablePyBytesRef",
    "MutablePyDictRef",
    "MutablePyFloatRef",
    "MutablePyFrozenSetRef",
    "MutablePyIntRef",
    "MutablePyListRef",
    "MutablePyObjectRef",
    "MutablePySetRef",
    "MutablePyStrRef",
    "MutablePyTupleRef",
    "MutableSequenceRef",
    "MutableSetRef",
    "MutableShapeRef",
    "OrderedMappingRef",
    "PrimitiveSet",
    "PyBoolRef",
    "PyBytesRef",
    "PyDictRef",
    "PyFloatRef",
    "PyFrozenSetRef",
    "PyIntRef",
    "PyListRef",
    "PyObjectRef",
    "PySetRef",
    "PyStrRef",
    "PyTupleRef",
    "ReactiveCollectionForm",
    "ReactiveItemRef",
    "ReactiveMappingRef",
    "ReactiveOrderedMappingRef",
    "ReactivePyBoolRef",
    "ReactivePyBytesRef",
    "ReactivePyDictRef",
    "ReactivePyFloatRef",
    "ReactivePyFrozenSetRef",
    "ReactivePyIntRef",
    "ReactivePyListRef",
    "ReactivePyObjectRef",
    "ReactivePySetRef",
    "ReactivePyStrRef",
    "ReactivePyTupleRef",
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
