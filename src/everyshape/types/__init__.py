"""Concrete type implementations for everyshape.

This module provides all concrete type implementations:
- IntType, FloatType, BoolType - Primitive numeric/boolean types
- StrType, BytesType - Text and binary types
- ListType, TupleType, DictType, SetType, FrozenSetType - Collection types
- NilType - None type
- AnyType - Dynamic/unknown type
- SentinelType, EmptyType, NAType - Special value types

Type-specific operations are in the respective type module's ops.py:
- everyshape.type.str.ops - String-specific operations
- everyshape.type.bytes.ops - Bytes-specific operations
- everyshape.type.dict.ops - Dict-specific operations
- everyshape.type.set.ops - Set-specific operations

Also, re-export bases ().
"""

from __future__ import annotations

from .any.type import AnyType
from .bases import (
    AddableBase,
    AdditiveBase,
    AndableBase,
    BitwiseAndableBase,
    BitwiseBase,
    BitwiseNotableBase,
    BitwiseOrableBase,
    BitwiseXorableBase,
    ComparisonBase,
    ContainableBase,
    DivisibleBase,
    EqualableBase,
    IndexableBase,
    IterableBase,
    LengthableBase,
    LogicalBase,
    MappingBase,
    ModuloableBase,
    MultiplicativeBase,
    MultiplyableBase,
    NegatableBase,
    NotableBase,
    NumericBase,
    OrableBase,
    OrderableBase,
    PowerableBase,
    SequenceBase,
    SetBase,
    ShiftableBase,
    SliceableBase,
    SubtractableBase,
    Type,
    UnionBaseType,
)
from .bool.type import BoolType
from .bytes.type import BytesType
from .dict.type import DictType
from .float.type import FloatType
from .int.type import IntType
from .list.type import ListType
from .none.type import NilType
from .sentinel.type import EmptyType, NAType, SentinelType
from .set.type import FrozenSetType, SetType
from .str.type import StrType
from .tuple.type import TupleType


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # CORE TYPE
    # ==========================================================================
    "Type",
    "UnionBaseType",
    # ==========================================================================
    # CAPABILITY BASES
    # ==========================================================================
    # Arithmetic bases
    "AddableBase",
    "AdditiveBase",
    "DivisibleBase",
    "ModuloableBase",
    "MultiplicativeBase",
    "MultiplyableBase",
    "NegatableBase",
    "NumericBase",
    "PowerableBase",
    "SubtractableBase",
    # Bitwise bases
    "BitwiseAndableBase",
    "BitwiseBase",
    "BitwiseNotableBase",
    "BitwiseOrableBase",
    "BitwiseXorableBase",
    "ShiftableBase",
    # Collection bases
    "ContainableBase",
    "IndexableBase",
    "IterableBase",
    "LengthableBase",
    "MappingBase",
    "SequenceBase",
    "SetBase",
    "SliceableBase",
    # Comparison bases
    "ComparisonBase",
    "EqualableBase",
    "OrderableBase",
    # Logical bases
    "AndableBase",
    "LogicalBase",
    "NotableBase",
    "OrableBase",
    # ==========================================================================
    # Types
    # ==========================================================================
    "AnyType",
    "BoolType",
    "BytesType",
    "DictType",
    "EmptyType",
    "FloatType",
    "FrozenSetType",
    "IntType",
    "ListType",
    "NAType",
    "NilType",
    "SentinelType",
    "SetType",
    "StrType",
    "TupleType",
]
