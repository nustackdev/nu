"""RValue system - computed values and expressions.

This module provides the foundational RValue system for the everyshape
data layer. RValues represent already computed/available values that
can be used in expressions and operations.

Hierarchy:
    RValueBase
    ├── LiteralBase (constant values)
    └── [Domain-specific values in everyverse]

Key components:
    - capabilities: Atomic capability protocols (Addable, Comparable, etc.)
    - primitives: Primitive type protocols (Number, String, Boolean)
    - collections: Collection protocols (Sequence, Mapping, Set)
    - base: RValueBase and LiteralBase base classes
    - bases: Reusable behavior mixins (ArithmeticBase, SequenceBase, etc.)

Example:
    >>> from everyshape.rvalue import RValueBase, LiteralBase
    >>> from everyshape.rvalue.primitives import Integer
    >>> from everyshape.rvalue.capabilities import is_addable
"""

# Base
from .base import (
    LiteralBase,
    RValueBase,
)

# Bases (mixins)
from .bases import (
    ArithmeticBase,
    BitwiseBase,
    ComparisonBase,
    LogicalBase,
    MappingBase,
    SequenceBase,
    StringBase,
)

# Capabilities
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

# Collections impl
from .collection_values import (
    DictValue,
    FrozenSetValue,
    ListValue,
    SetValue,
    TupleValue,
)

# Collections
from .collections import (
    Collection,
    Container,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set,
)

# Literal conversion
from .conversion import literal

# Primitives impl
from .primitive_values import (
    BoolValue,
    BytesValue,
    FloatValue,
    IntValue,
    NoneValue,
    StrValue,
)

# Primitives
from .primitives import (
    Boolean,
    Bytes,
    Floating,
    Integer,
    Number,
    String,
)


__all__ = [  # noqa: RUF022
    # Capabilities
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
    # Primitives
    "Boolean",
    "Bytes",
    "Floating",
    "Integer",
    "Number",
    "String",
    # Collections
    "Collection",
    "Container",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Sequence",
    "Set",
    # Base
    "LiteralBase",
    "RValueBase",
    # Bases (mixins)
    "ArithmeticBase",
    "BitwiseBase",
    "ComparisonBase",
    "LogicalBase",
    "MappingBase",
    "SequenceBase",
    "StringBase",
    # Primitives
    "IntValue",
    "FloatValue",
    "BoolValue",
    "StrValue",
    "BytesValue",
    "NoneValue",
    # Collections
    "ListValue",
    "DictValue",
    "TupleValue",
    "SetValue",
    "FrozenSetValue",
    # Conversion
    "literal",
]
