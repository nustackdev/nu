"""Type system bases for Term expressions.

This module provides the type system bases for everyshape:
- Type[T] - Base class for typed expressions
- Capability mixins: NumericBase, ComparisonBase, LogicalBase, etc.

Concrete type implementations are in everyshape.type:
- everyshape.type.int.IntType
- everyshape.type.float.FloatType
- everyshape.type.str.StrType
- etc.

Hierarchy:
    +-- Arithmetic Bases
    |   +-- AddableBase         - __add__, __radd__
    |   +-- SubtractableBase    - __sub__, __rsub__
    |   +-- NegatableBase       - __neg__, __pos__, __abs__
    |   +-- AdditiveBase        - Combines Add + Sub + Negatable
    |   +-- MultiplyableBase    - __mul__, __rmul__
    |   +-- DivisibleBase       - __truediv__, __rtruediv__, __floordiv__, __rfloordiv__
    |   +-- ModuloableBase      - __mod__, __rmod__
    |   +-- PowerableBase       - __pow__, __rpow__
    |   +-- MultiplicativeBase  - Combines Multiply + Divide + Modulo + Power
    |   +-- NumericBase         - Combines Additive + Multiplicative (full arithmetic)
    +-- Comparison Bases
    |   +-- OrderableBase       - __gt__, __lt__, __ge__, __le__
    |   +-- EqualableBase       - eq(), ne(), is_()
    |   +-- ComparisonBase      - Combines Orderable + Equalable
    +-- Logical Bases
    |   +-- AndableBase         - and_()
    |   +-- OrableBase          - or_()
    |   +-- NotableBase         - not_(), bool_()
    |   +-- LogicalBase         - Combines all logical ops
    +-- Bitwise Bases
    |   +-- BitwiseAndableBase  - bitand()
    |   +-- BitwiseOrableBase   - bitor()
    |   +-- BitwiseXorableBase  - __xor__, __rxor__
    |   +-- BitwiseNotableBase  - bitnot()
    |   +-- ShiftableBase       - __lshift__, __rshift__ and reverse
    |   +-- BitwiseBase         - Combines all bitwise ops
    +-- Collection Bases
    |   +-- LengthableBase      - len_()
    |   +-- IndexableBase       - __getitem__ for int keys
    |   +-- SliceableBase       - __getitem__ for slices, slice_()
    |   +-- ContainableBase     - contains()
    |   +-- IterableBase        - map_(), filter_(), reduce_(), etc.
    |   +-- SequenceBase        - Combines collection ops for sequences
    |   +-- MappingBase         - Combines collection ops for mappings
    |   +-- SetBase             - Combines collection ops for sets

Example:
    >>> from .bases import Type, NumericBase
    >>> from everyshape.type import IntType
    >>>
    >>> x = IntType(42)
    >>> x.execute(ctx)  # Returns 42
"""

from __future__ import annotations

# Arithmetic bases
from .base_arithmetic import (
    AddableBase,
    AdditiveBase,
    DivisibleBase,
    ModuloableBase,
    MultiplicativeBase,
    MultiplyableBase,
    NegatableBase,
    NumericBase,
    PowerableBase,
    SubtractableBase,
)

# Bitwise bases
from .base_bitwise import (
    BitwiseAndableBase,
    BitwiseBase,
    BitwiseNotableBase,
    BitwiseOrableBase,
    BitwiseXorableBase,
    ShiftableBase,
)

# Collection bases
from .base_collections import (
    ContainableBase,
    IndexableBase,
    IterableBase,
    LengthableBase,
    MappingBase,
    SequenceBase,
    SetBase,
    SliceableBase,
)

# Comparison bases
from .base_comparison import ComparisonBase, EqualableBase, OrderableBase

# Logical bases
from .base_logical import AndableBase, LogicalBase, NotableBase, OrableBase

# Core Type class
from .type import BaseType


type UnionBaseType = (
    BaseType
    | AddableBase
    | SubtractableBase
    | NegatableBase
    | MultiplyableBase
    | DivisibleBase
    | ModuloableBase
    | PowerableBase
    | AdditiveBase
    | MultiplicativeBase
    | NumericBase
    | OrderableBase
    | EqualableBase
    | ComparisonBase
    | AndableBase
    | OrableBase
    | NotableBase
    | LogicalBase
    | BitwiseAndableBase
    | BitwiseOrableBase
    | BitwiseXorableBase
    | BitwiseNotableBase
    | ShiftableBase
    | BitwiseBase
    | LengthableBase
    | IndexableBase
    | SliceableBase
    | ContainableBase
    | IterableBase
    | SequenceBase
    | MappingBase
    | SetBase
)


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # CORE TYPE
    # ==========================================================================
    "BaseType",
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
]
