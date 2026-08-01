"""Nu shape fabric: DSL + Ref blueprints (3-tier matrix) + queries/commands.

Public surface:
- ``Shape``, ``ShapeMeta``, ``Slot``, ``SlotDescriptor`` — the DSL.
- 21 Ref blueprints for structural navigation and substrate extension (7 families x 3 tiers).
- ``SetCommand``, ``EraseCommand`` — slot-level write commands.
- ``LoadQuery``, ``ExistsQuery``, ``MissingQuery``, ``ExtractQuery``,
  ``AdvanceCursorQuery`` — slot-level read queries.

Reactive queries (``OnChangeQuery`` / ``OnChildChangeQuery`` /
``OnChildrenChangeQuery`` / ``OnDescendantsChangeQuery`` /
``OnPrimitiveChangeQuery``) live in ``nu.core.reactive`` -- one unified
interface for every substrate, reached through the shape Form mixins.
"""

from __future__ import annotations

from .dsl import Shape, ShapeMeta, Slot, SlotDescriptor
from .interactions import (
    AdvanceCursorQuery,
    EraseCommand,
    ExistsQuery,
    ExtractQuery,
    LoadQuery,
    MissingQuery,
    PrimitiveSetCommand,
    SetCommand,
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
    "PrimitiveSetCommand",
    "ReactiveItemRef",
    "ReactiveMappingRef",
    "ReactiveSequenceRef",
    "ReactiveSetRef",
    "ReactiveShapeRef",
    "ReactiveShapesMappingRef",
    "ReactiveShapesSequenceRef",
    "SequenceRef",
    "SetCommand",
    "SetRef",
    # DSL
    "Shape",
    "ShapeMeta",
    "ShapeRef",
    "ShapesMappingRef",
    "ShapesSequenceRef",
    "Slot",
    "SlotDescriptor",
]
