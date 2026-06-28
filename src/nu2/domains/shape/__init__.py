"""Nu shape fabric: DSL + Ref blueprints (3-tier matrix) + queries/commands/reactive.

Public surface:
- ``Shape``, ``ShapeMeta``, ``Slot``, ``SlotDescriptor`` — the DSL.
- 21 Ref blueprints for structural navigation and substrate extension (7 families x 3 tiers).
- ``StoreCommand``, ``EraseCommand`` — slot-level write commands.
- ``LoadQuery``, ``ExistsQuery``, ``MissingQuery``, ``ExtractQuery``,
  ``AdvanceCursorQuery`` — slot-level read queries.
- ``OnChangeQuery`` — generic reactive query (any observable Ref).
- ``OnChildChangeQuery``, ``OnChildrenChangeQuery``, ``OnDescendantsChangeQuery``
  — shape-domain reactive queries (require structured Refs with tree structure).
"""

from __future__ import annotations

from nu2.domains.shape.interactions import (
    OnChildChangeQuery,
    OnChildrenChangeQuery,
    OnDescendantsChangeQuery,
)
from nu2.forms.reactive import OnChangeQuery

from .dsl import Shape, ShapeMeta, Slot, SlotDescriptor
from .interactions import (
    AdvanceCursorQuery,
    EraseCommand,
    ExistsQuery,
    ExtractQuery,
    LoadQuery,
    MissingQuery,
    PrimitiveStoreCommand,
    StoreCommand,
)
from .refs import (
    ItemRef,
    MappingRef,
    MutableItemRef,
    MutableMappingRef,
    MutableSequenceRef,
    MutableSetRef,
    MutableShapeRef,
    MutableShapesMappingRef,
    MutableShapesSequenceRef,
    ReactiveItemRef,
    ReactiveMappingRef,
    ReactiveSequenceRef,
    ReactiveSetRef,
    ReactiveShapeRef,
    ReactiveShapesMappingRef,
    ReactiveShapesSequenceRef,
    SequenceRef,
    SetRef,
    ShapeRef,
    ShapesMappingRef,
    ShapesSequenceRef,
)


__all__ = [
    # Queries
    "AdvanceCursorQuery",
    # Commands
    "EraseCommand",
    "ExistsQuery",
    "ExtractQuery",
    # Item Refs
    "ItemRef",
    "LoadQuery",
    # Mapping Refs
    "MappingRef",
    "MissingQuery",
    "MutableItemRef",
    "MutableMappingRef",
    # Sequence Refs
    "MutableSequenceRef",
    # Set Refs
    "MutableSetRef",
    # Shape Refs
    "MutableShapeRef",
    # ShapesMapping Refs
    "MutableShapesMappingRef",
    # ShapesSequence Refs
    "MutableShapesSequenceRef",
    # Reactive Queries
    "OnChangeQuery",
    "OnChildChangeQuery",
    "OnChildrenChangeQuery",
    "OnDescendantsChangeQuery",
    "PrimitiveStoreCommand",
    "ReactiveItemRef",
    "ReactiveMappingRef",
    "ReactiveSequenceRef",
    "ReactiveSetRef",
    "ReactiveShapeRef",
    "ReactiveShapesMappingRef",
    "ReactiveShapesSequenceRef",
    "SequenceRef",
    "SetRef",
    # DSL
    "Shape",
    "ShapeMeta",
    "ShapeRef",
    "ShapesMappingRef",
    "ShapesSequenceRef",
    "Slot",
    "SlotDescriptor",
    "StoreCommand",
]
