"""Type system for Term expressions.

This module provides the unified Type system for everyshape, including:
- Type[T] - Base class for typed expressions
- Concrete types: IntType, FloatType, StrType, BoolType, etc.
- Capability mixins: NumericBase, ComparisonBase, LogicalBase, etc.

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

Type Hierarchy:
    Type[T] (base from term.py)
    ├── IntType               # int expressions
    ├── FloatType             # float expressions
    ├── StrType               # str expressions
    ├── BoolType              # bool expressions
    ├── BytesType             # bytes expressions
    ├── NilType               # None expressions
    ├── ListType[T]           # list expressions
    ├── DictType[K, V]        # dict expressions
    ├── SetType[T]            # set expressions
    ├── TupleType[*Ts]        # tuple expressions
    ├── FrozenSetType[T]      # frozenset expressions
    ├── AnyType               # dynamic/unknown type
    └── SentinelType          # special values
        ├── EmptyType         # absence of value
        └── NAType            # not applicable

Example:
    >>> from everyshape.term.type import IntType
    >>>
    >>> x = IntType(42)
    >>> x.execute(ctx)  # Returns 42
"""

from __future__ import annotations

from .any_type import AnyType

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

# Concrete types
from .bool_type import BoolType
from .bytes_type import BytesType
from .dict_type import DictType
from .float_type import FloatType
from .int_type import IntType
from .list_type import ListType
from .none_type import NilType
from .sentinel import EmptyType, NAType, SentinelType
from .set_type import FrozenSetType, SetType
from .str_type import StrType
from .tuple_type import TupleType

# Core Type class
from .type import Type


type UnionBaseType = (
    Type
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
    # CONCRETE TYPES
    # ==========================================================================
    # Primitive types
    "AnyType",
    "BoolType",
    "BytesType",
    "FloatType",
    "IntType",
    "NilType",
    "StrType",
    # Collection types
    "DictType",
    "FrozenSetType",
    "ListType",
    "SetType",
    "TupleType",
    # Sentinel types
    "EmptyType",
    "NAType",
    "SentinelType",
]
