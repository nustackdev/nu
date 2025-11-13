"""Shape extensions."""

from __future__ import annotations

from .commands import SetCmd, StoreCmd
from .operations import ExtractOp, GetOp
from .refs import ShapeRef, ValueRef
from .slots import ShapeSlot, ValueSlot


__all__ = [
    "ExtractOp",
    "GetOp",
    "SetCmd",
    "ShapeRef",
    "ShapeSlot",
    "StoreCmd",
    "ValueRef",
    "ValueSlot",
]
