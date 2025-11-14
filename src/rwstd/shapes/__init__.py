"""Shape extensions."""

from __future__ import annotations

from .commands import AppendCmd, SetCmd, StoreCmd
from .operations import ExtractOp, GetOp
from .refs import (
    MappingRef,
    MappingShapeRef,
    MappingValueRef,
    SequenceRef,
    SequenceShapeRef,
    SequenceValueRef,
    ShapeRef,
    ValueRef,
)
from .shape import Shape
from .slots import (
    MappingShapeSlot,
    MappingSlot,
    PrimitiveSlot,
    SequenceShapeSlot,
    SequenceSlot,
    ShapeSlot,
)


__all__ = [
    "AppendCmd",
    "ExtractOp",
    "GetOp",
    "MappingRef",
    "MappingShapeRef",
    "MappingShapeSlot",
    "MappingSlot",
    "MappingValueRef",
    "PrimitiveSlot",
    "SequenceRef",
    "SequenceShapeRef",
    "SequenceShapeSlot",
    "SequenceSlot",
    "SequenceValueRef",
    "SetCmd",
    "Shape",
    "ShapeRef",
    "ShapeSlot",
    "StoreCmd",
    "ValueRef",
]
