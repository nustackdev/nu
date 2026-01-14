"""Type system - unified typed expressions.

This module provides the unified Type system for everyshape.
Types handle both literal and computed values through a single interface.

Module Structure:
    types.py         - Unified Type classes (IntType, StrType, etc.)
    bases.py         - Capability implementation mixins (NumericBase, etc.)
    capabilities.py  - Atomic capability protocols (Addable, Comparable, etc.)
    conversion.py    - Conversion utilities (literal, computed)

Type Hierarchy:
    Type[T] (unified typed expression)
    ├── IntType, FloatType, StrType, BoolType, BytesType, NilType
    ├── ListType[T], DictType[K, V], SetType[T], TupleType[*Ts], FrozenSetType[T]
    ├── AnyType (dynamic/unknown)
    └── SentinelType (EmptyType, NAType)

Capability Bases:
    CoreBase                    - Everyone inherits (ifelse, is_empty, is_na)
    ├── Arithmetic Bases
    │   ├── NumericBase         - Full arithmetic (+, -, *, /, etc.)
    │   ├── AdditiveBase        - Addition/subtraction only
    │   └── MultiplicativeBase  - Multiplication family only
    ├── ComparisonBase          - Ordering and equality
    ├── LogicalBase             - and_(), or_(), not_()
    ├── BitwiseBase             - Bit operations
    ├── SequenceBase            - List/tuple operations
    ├── MappingBase             - Dict operations
    └── StringBase              - String operations

Example:
    >>> from everyshape.term.types import IntType, literal
    >>>
    >>> # Create from literal value
    >>> x = IntType(42)
    >>> x.execute(ctx)  # Returns 42
    >>>
    >>> # Use literal() for automatic wrapping
    >>> val = literal(42)  # Returns IntType(42)
"""

# Capability implementation mixins
from .bases import (  # noqa: I001
    # Core base (everyone needs)
    CoreBase,
    # Atomic arithmetic bases
    AddableBase,
    SubtractableBase,
    NegatableBase,
    MultiplyableBase,
    DivisibleBase,
    ModuloableBase,
    PowerableBase,
    # Combined arithmetic bases
    AdditiveBase,
    MultiplicativeBase,
    NumericBase,
    # Comparison bases
    OrderableBase,
    EqualableBase,
    ComparisonBase,
    # Logical bases
    AndableBase,
    OrableBase,
    NotableBase,
    LogicalBase,
    # Bitwise bases
    BitwiseAndableBase,
    BitwiseOrableBase,
    BitwiseXorableBase,
    BitwiseNotableBase,
    ShiftableBase,
    BitwiseBase,
    # Collection bases
    LengthableBase,
    IndexableBase,
    SliceableBase,
    ContainableBase,
    IterableBase,
    SequenceBase,
    MappingBase,
    # Set bases
    SetBase,
    # String bases
    ConcatenableBase,
    StringBase,
    StringMethodsBase,
    # Bytes bases
    BytesMethodsBase,
)

# Capability protocols
from .capabilities import (
    Absoluteable,
    Addable,
    Andable,
    BitwiseAndable,
    BitwiseInvertible,
    BitwiseOrable,
    BitwiseXorable,
    Comparable,
    Concatenable,
    Containable,
    Divisible,
    Equalable,
    FloorDivisible,
    Formattable,
    Indexable,
    Invertible,
    Iterable,
    LeftShiftable,
    Lengthable,
    Modulable,
    Multipliable,
    Negatable,
    Orable,
    Powerable,
    RightShiftable,
    Sliceable,
    Subtractable,
    is_addable,
    is_andable,
    is_comparable,
    is_containable,
    is_divisible,
    is_equalable,
    is_indexable,
    is_iterable,
    is_lengthable,
    is_multipliable,
    is_orable,
    is_sliceable,
    is_subtractable,
)

# Conversion utilities
from .conversion import computed, literal

# Unified Type classes
from .definitions import (
    # Primitive types
    SentinelType,
    IntType,
    FloatType,
    StrType,
    BoolType,
    BytesType,
    NilType,
    ListType,
    DictType,
    TupleType,
    SetType,
    FrozenSetType,
    AnyType,
    EmptyType,
    NAType,
)

# Backwards compatibility - re-export literal types as aliases to unified types
# These are DEPRECATED - use *Type classes directly
IntLiteral = IntType
FloatLiteral = FloatType
StrLiteral = StrType
BoolLiteral = BoolType
BytesLiteral = BytesType
NoneLiteral = NilType
ListLiteral = ListType
DictLiteral = DictType
TupleLiteral = TupleType
SetLiteral = SetType
FrozenSetLiteral = FrozenSetType


__all__ = [  # noqa: RUF022
    # ==========================================================================
    # CAPABILITY IMPLEMENTATION MIXINS
    # ==========================================================================
    # Core base
    "CoreBase",
    # Atomic arithmetic
    "AddableBase",
    "SubtractableBase",
    "NegatableBase",
    "MultiplyableBase",
    "DivisibleBase",
    "ModuloableBase",
    "PowerableBase",
    # Combined arithmetic
    "AdditiveBase",
    "MultiplicativeBase",
    "NumericBase",
    # Comparison
    "OrderableBase",
    "EqualableBase",
    "ComparisonBase",
    # Logical
    "AndableBase",
    "OrableBase",
    "NotableBase",
    "LogicalBase",
    # Bitwise
    "BitwiseAndableBase",
    "BitwiseOrableBase",
    "BitwiseXorableBase",
    "BitwiseNotableBase",
    "ShiftableBase",
    "BitwiseBase",
    # Collection
    "LengthableBase",
    "IndexableBase",
    "SliceableBase",
    "ContainableBase",
    "IterableBase",
    "SequenceBase",
    "MappingBase",
    # Set
    "SetBase",
    # String
    "ConcatenableBase",
    "StringBase",
    "StringMethodsBase",
    # Bytes
    "BytesMethodsBase",
    # ==========================================================================
    # CAPABILITY PROTOCOLS
    # ==========================================================================
    "Absoluteable",
    "Addable",
    "Andable",
    "BitwiseAndable",
    "BitwiseInvertible",
    "BitwiseOrable",
    "BitwiseXorable",
    "Comparable",
    "Concatenable",
    "Containable",
    "Divisible",
    "Equalable",
    "FloorDivisible",
    "Formattable",
    "Indexable",
    "Invertible",
    "Iterable",
    "LeftShiftable",
    "Lengthable",
    "Modulable",
    "Multipliable",
    "Negatable",
    "Orable",
    "Powerable",
    "RightShiftable",
    "Sliceable",
    "Subtractable",
    # Type guards
    "is_addable",
    "is_andable",
    "is_comparable",
    "is_containable",
    "is_divisible",
    "is_equalable",
    "is_indexable",
    "is_iterable",
    "is_lengthable",
    "is_multipliable",
    "is_orable",
    "is_sliceable",
    "is_subtractable",
    # ==========================================================================
    # UNIFIED TYPE CLASSES (NEW - USE THESE)
    # ==========================================================================
    # Primitive types
    "IntType",
    "FloatType",
    "StrType",
    "BoolType",
    "BytesType",
    "NilType",
    # Collection types
    "ListType",
    "DictType",
    "TupleType",
    "SetType",
    "FrozenSetType",
    # Special types
    "AnyType",
    "SentinelType",
    "EmptyType",
    "NAType",
    # ==========================================================================
    # BACKWARDS COMPATIBILITY (DEPRECATED)
    # ==========================================================================
    # Old computed value names → now unified types
    "IntType",
    "FloatType",
    "BoolType",
    "StrType",
    "BytesType",
    "NilType",
    "AnyType",
    "EmptyType",
    "NAType",
    "ListType",
    "DictType",
    "TupleType",
    "SetType",
    "FrozenSetType",
    # Old literal names → now unified types
    "IntLiteral",
    "FloatLiteral",
    "BoolLiteral",
    "StrLiteral",
    "BytesLiteral",
    "NoneLiteral",
    "ListLiteral",
    "DictLiteral",
    "TupleLiteral",
    "SetLiteral",
    "FrozenSetLiteral",
    # ==========================================================================
    # CONVERSION UTILITIES
    # ==========================================================================
    "literal",
    "computed",
]
