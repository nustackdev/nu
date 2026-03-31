"""Primitive and service refs -- direct Context lookup.

PrimRef: flat name-based lookup from ctx.attrs.
ServiceRef: type-based lookup from ctx bindings.
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
from .service import ServiceRef
from .service_morphisms import ServiceExistsOp, ServiceGetOp


__all__ = [
    "AnyRef",
    "BoolRef",
    "BytesRef",
    "FloatRef",
    "IntRef",
    "PrimExistsOp",
    "PrimGetOp",
    "PrimRef",
    "ServiceExistsOp",
    "ServiceGetOp",
    "ServiceRef",
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
