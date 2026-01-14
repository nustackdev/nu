"""Capability implementation bases for RValue types.

This module provides hierarchical mixin classes that implement value capabilities.
The hierarchy allows fine-grained composition while providing convenient combined bases.

Hierarchy:
    CoreBase                    - Everyone inherits this (ifelse, is_empty, is_nan, is_sentinel)
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
    +-- String Bases
        +-- ConcatenableBase    - __add__ for strings
        +-- StringBase          - String-specific operations

Usage:
    class MyIntValue(NumericBase, ComparisonBase, BitwiseBase, CoreBase, Literal[int]):
        # Gets full numeric, comparison, and bitwise operations
        pass

    class MyDecimalValue(AdditiveBase, MultiplyableBase, ComparisonBase, CoreBase, Literal):
        # Gets addition, multiplication (no floor div, mod, pow), and comparison
        pass
"""

from .arithmetic import (
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
from .bitwise import (
    BitwiseAndableBase,
    BitwiseBase,
    BitwiseNotableBase,
    BitwiseOrableBase,
    BitwiseXorableBase,
    ShiftableBase,
)
from .bytes import BytesMethodsBase
from .collection import (
    ContainableBase,
    IndexableBase,
    IterableBase,
    LengthableBase,
    MappingBase,
    SequenceBase,
    SetBase,
    SliceableBase,
)
from .comparison import ComparisonBase, EqualableBase, OrderableBase
from .core import CoreBase
from .logical import AndableBase, LogicalBase, NotableBase, OrableBase
from .string import ConcatenableBase, StringBase, StringMethodsBase


__all__ = [  # noqa: RUF022
    # Core types
    "CoreBase",
    "UnionBaseType",
    # Atomic arithmetic bases
    "AddableBase",
    "SubtractableBase",
    "NegatableBase",
    "MultiplyableBase",
    "DivisibleBase",
    "ModuloableBase",
    "PowerableBase",
    # Combined arithmetic bases
    "AdditiveBase",
    "MultiplicativeBase",
    "NumericBase",
    # Comparison bases
    "OrderableBase",
    "EqualableBase",
    "ComparisonBase",
    # Logical bases
    "AndableBase",
    "OrableBase",
    "NotableBase",
    "LogicalBase",
    # Bitwise bases
    "BitwiseAndableBase",
    "BitwiseOrableBase",
    "BitwiseXorableBase",
    "BitwiseNotableBase",
    "ShiftableBase",
    "BitwiseBase",
    # Collection bases
    "LengthableBase",
    "IndexableBase",
    "SliceableBase",
    "ContainableBase",
    "IterableBase",
    "SequenceBase",
    "MappingBase",
    # Set bases
    "SetBase",
    # String bases
    "ConcatenableBase",
    "StringBase",
    "StringMethodsBase",
    # Bytes bases
    "BytesMethodsBase",
]


# =============================================================================
# UNION BASE TYPE
# =============================================================================

type UnionBaseType = (
    CoreBase
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
    | ConcatenableBase
    | StringBase
    | StringMethodsBase
    | BytesMethodsBase
)
