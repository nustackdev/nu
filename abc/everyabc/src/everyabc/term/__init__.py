"""Term system — semantic contracts for executable nodes.

    Term[ResultT]           — executable node (0-cell)
    ├── LValue[T]           — addressable location
    │   └── Ref[T]          — typed reference
    └── RValue[ResultT]     — evaluable expression
        ├── Value[T]        — typed value holder
        └── Morphism[T]     — transformation
            └── NAryMorphism    — with operand management
                ├── UnaryMorphism
                ├── BinaryMorphism
                └── TernaryMorphism

Purity mixins (orthogonal to arity):
    - Operation: pure computation (no side effects)
    - Command: impure mutation (has side effects)

Sentinels:
    - Empty: value doesn't exist
    - Invalid: operation not applicable
"""

from __future__ import annotations

from .arg import (
    Arg,
    BoolArg,
    BytesArg,
    DictArg,
    FloatArg,
    FrozenSetArg,
    IntArg,
    ListArg,
    NoneArg,
    SetArg,
    StrArg,
    TupleArg,
)
from .morphism import (
    BinaryCommand,
    BinaryMorphism,
    BinaryOperation,
    Command,
    Morphism,
    NAryCommand,
    NAryMorphism,
    NAryOperation,
    Operation,
    TernaryCommand,
    TernaryMorphism,
    TernaryOperation,
    UnaryCommand,
    UnaryMorphism,
    UnaryOperation,
)
from .ref import Ref
from .sentinel import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    Sentinel,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)
from .term import (
    LValue,
    RValue,
    Term,
    Value,
)


__all__ = [  # noqa: RUF022
    # Term hierarchy
    "Term",
    "LValue",
    "RValue",
    "Value",
    # References
    "Ref",
    # Morphisms
    "Morphism",
    "NAryMorphism",
    "UnaryMorphism",
    "BinaryMorphism",
    "TernaryMorphism",
    # Purity mixins
    "Operation",
    "Command",
    # Purity + arity
    "NAryOperation",
    "NAryCommand",
    "UnaryOperation",
    "UnaryCommand",
    "BinaryOperation",
    "BinaryCommand",
    "TernaryOperation",
    "TernaryCommand",
    # Sentinel
    "Sentinel",
    "Empty",
    "Invalid",
    "EMPTY",
    "INVALID",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
    # Arg types
    "Arg",
    "IntArg",
    "FloatArg",
    "StrArg",
    "BoolArg",
    "BytesArg",
    "NoneArg",
    "ListArg",
    "DictArg",
    "SetArg",
    "FrozenSetArg",
    "TupleArg",
]
