"""RValue system - computed values and expressions.

This module provides the foundational RValue system for the everyshape
data layer. RValues represent already computed/available values that
can be used in expressions and operations.

Module Structure:
    capabilities.py      - Atomic capability PROTOCOLS (Addable, Comparable, etc.)
    bases.py             - Capability implementation MIXINS (NumericBase, etc.)
    literals.py          - Literal value types (IntLiteral, StrLiteral, etc.)
    primitive_values.py  - Computed primitive types (IntValue, StrValue, etc.)
    collection_values.py - Computed collection types (ListValue, DictValue, etc.)
    conversion.py        - Conversion utilities (literal, result)

Value Types:
    Literal Values (wrap fixed Python values):
        IntLiteral, FloatLiteral, BoolLiteral, StrLiteral, BytesLiteral, NoneLiteral
        ListLiteral, DictLiteral, TupleLiteral, SetLiteral, FrozenSetLiteral

    Computed Values (wrap Operations/RValues):
        IntValue, FloatValue, BoolValue, StrValue, BytesValue, NoneValue
        ListValue, DictValue, TupleValue, SetValue, FrozenSetValue

    Special Values:
        UnknownValue - Dynamic/unknown type
        EmptyValue   - Absence of value
        NaNValue     - Not-a-number

Hierarchy:
    CoreBase                    - Everyone inherits (ifelse, is_empty, is_nan)
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
    >>> from everyshape.shape.values import IntLiteral, literal
    >>>
    >>> # Create literal value
    >>> lit = IntLiteral(42)
    >>> lit.execute(ctx)  # Returns 42
    >>>
    >>> # Use literal() for automatic wrapping
    >>> val = literal(42)  # Returns IntLiteral(42)
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
from .conversion import literal, computed

# Literal types
from .literals import (
    BoolLiteral,
    BytesLiteral,
    DictLiteral,
    FloatLiteral,
    FrozenSetLiteral,
    IntLiteral,
    ListLiteral,
    NoneLiteral,
    SetLiteral,
    StrLiteral,
    TupleLiteral,
)

# Computed types
from .values import (
    BoolValue,
    BytesValue,
    EmptyValue,
    FloatValue,
    IntValue,
    NaNValue,
    NoneValue,
    StrValue,
    UnknownValue,
    DictValue,
    FrozenSetValue,
    ListValue,
    SetValue,
    TupleValue,
)


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
    # LITERAL VALUE TYPES
    # ==========================================================================
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
    # COMPUTED PRIMITIVE VALUE TYPES
    # ==========================================================================
    "IntValue",
    "FloatValue",
    "BoolValue",
    "StrValue",
    "BytesValue",
    "NoneValue",
    # ==========================================================================
    # SPECIAL VALUE TYPES
    # ==========================================================================
    "UnknownValue",
    "EmptyValue",
    "NaNValue",
    # ==========================================================================
    # COMPUTED COLLECTION VALUE TYPES
    # ==========================================================================
    "ListValue",
    "DictValue",
    "TupleValue",
    "SetValue",
    "FrozenSetValue",
    # ==========================================================================
    # CONVERSION UTILITIES
    # ==========================================================================
    "literal",
    "computed",
]
