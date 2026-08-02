"""Nu shape fabric: DSL + Ref blueprints (3-tier matrix) + queries/commands.

Public surface:
- ``Shape``, ``ShapeMeta``, ``Slot``, ``SlotDescriptor``: the DSL.
- 21 Ref blueprints for structural navigation and substrate extension (7 families x 3 tiers).
- ``SetCmd``, ``Erase``: slot-level write commands.
- ``Load``, ``Exists``, ``Missing``, ``Extract``,
  ``AdvanceCursor``: slot-level read queries.

Reactive queries (``OnChange`` / ``OnChildChange`` /
``OnChildrenChange`` / ``OnDescendantsChange`` /
``OnPrimitiveChange``) live in ``nu.core.reactive`` -- one unified
interface for every substrate, reached through the shape Form mixins.
"""

from __future__ import annotations

from .dsl import Shape, ShapeMeta, Slot, SlotDescriptor
from .interactions import (
    AdvanceCursor,
    Erase,
    Exists,
    Extract,
    Load,
    Missing,
    PrimitiveSet,
    SetCmd,
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
    "AdvanceCursor",
    # Commands
    "Erase",
    "Exists",
    "Extract",
    # Item Refs
    "ItemRef",
    "Load",
    # Mapping Refs
    "MappingRef",
    "Missing",
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
    "PrimitiveSet",
    "ReactiveItemRef",
    "ReactiveMappingRef",
    "ReactiveSequenceRef",
    "ReactiveSetRef",
    "ReactiveShapeRef",
    "ReactiveShapesMappingRef",
    "ReactiveShapesSequenceRef",
    "SequenceRef",
    "SetCmd",
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
