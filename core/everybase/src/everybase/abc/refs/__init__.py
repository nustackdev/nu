"""Primitive refs — flat name-based Context lookup.

Typed ref constructions that resolve by name directly from ctx.
"""

from __future__ import annotations

from ..types import (
    AnyType,
    BoolType,
    BytesType,
    FloatType,
    IntType,
    StrType,
)
from .base import PrimRef
from .morphisms import PrimExistsOp, PrimGetOp


__all__ = [
    "AnyRef",
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "PrimExistsOp",
    "PrimGetOp",
    "PrimRef",
    "StrRef",
]


class IntRef(PrimRef[int], IntType):
    """Primitive int ref."""

    value_type = int


class FloatRef(PrimRef[float], FloatType):
    """Primitive float ref."""

    value_type = float


class StrRef(PrimRef[str], StrType):
    """Primitive str ref."""

    value_type = str


class BoolRef(PrimRef[bool], BoolType):
    """Primitive bool ref."""

    value_type = bool


class BytesRef(PrimRef[bytes], BytesType):
    """Primitive bytes ref."""

    value_type = bytes


class AnyRef(PrimRef[object], AnyType):
    """Primitive any ref."""

    value_type = object
