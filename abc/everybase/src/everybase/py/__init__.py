"""Concrete Python memory refs for everybase.

This module provides concrete ref implementations for Python types.
Each inherits from PyRefBase (source storage) and its type-specific
RefBase (traits).

Hierarchy:
    RefBase (in refs/) - pure ABC with ergonomics
    └── XxxRefBase (in refs/) - combines traits

    PyRefBase (in py/) - source storage mixin

    XxxRef(PyRefBase, XxxRefBase) - concrete py ref

Types:
    Primitives: IntRef, FloatRef, BoolRef, StrRef, BytesRef
    Collections: ListRef, DictRef, SetRef, FrozenSetRef, TupleRef
    Special: AnyRef, NoneRef, SentinelRef, EmptyRef, InvalidRef
"""

from __future__ import annotations

# Special
from .any import AnyRef

# Base
from .base import PyRefBase

# Primitives
from .bool import BoolRef
from .bytes import BytesRef

# Collections
from .dict import DictRef
from .float import FloatRef
from .frozenset import FrozenSetRef
from .int import IntRef
from .list import ListRef
from .none import NoneRef
from .sentinel import EmptyRef, InvalidRef, SentinelRef
from .set import SetRef
from .str import StrRef
from .tuple import TupleRef


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
