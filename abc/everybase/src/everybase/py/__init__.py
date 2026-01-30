"""Concrete Python memory refs for everybase.

Each ref combines PyRefBase (source storage) with its type-specific
RefBase (capability traits).

Types:
    Primitives: IntRef, FloatRef, BoolRef, StrRef, BytesRef
    Collections: ListRef, DictRef, SetRef, FrozenSetRef, TupleRef
    Special: AnyRef, NoneRef, SentinelRef, EmptyRef, InvalidRef
"""

from __future__ import annotations

from .base import PyRefBase
from .refs import (
    AnyRef,
    BoolRef,
    BytesRef,
    DictRef,
    EmptyRef,
    FloatRef,
    FrozenSetRef,
    IntRef,
    InvalidRef,
    ListRef,
    NoneRef,
    SentinelRef,
    SetRef,
    StrRef,
    TupleRef,
)


__all__ = [
    "AnyRef",
    "BoolRef",
    "BytesRef",
    "DictRef",
    "EmptyRef",
    "FloatRef",
    "FrozenSetRef",
    "IntRef",
    "InvalidRef",
    "ListRef",
    "NoneRef",
    "PyRefBase",
    "SentinelRef",
    "SetRef",
    "StrRef",
    "TupleRef",
]
