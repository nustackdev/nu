"""Shape extensions."""

from __future__ import annotations

from .commands import AppendCmd, SetCmd, StoreCmd
from .operations import ExtractOp, GetOp
from .refs import MappingRef, MappingValueRef, SequenceRef, SequenceValueRef, ShapeRef, ValueRef
from .slots import MappingSlot, PrimitiveSlot, SequenceSlot, ShapeSlot


__all__ = [
    "AppendCmd",
    "ExtractOp",
    "GetOp",
    "MappingRef",
    "MappingSlot",
    "MappingValueRef",
    "PrimitiveSlot",
    "SequenceRef",
    "SequenceSlot",
    "SequenceValueRef",
    "SetCmd",
    "ShapeRef",
    "ShapeSlot",
    "StoreCmd",
    "ValueRef",
]
