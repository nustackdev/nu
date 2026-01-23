"""Every - Core primitives for the every ecosystem."""

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
from .flow import Flow, Path, Runtime
from .protocols import Gettable, Settable
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
    BinaryMorphism,
    Command,
    Context,
    LValue,
    Morphism,
    NAryMorphism,
    Operation,
    Ref,
    RValue,
    Shape,
    ShapeMeta,
    Slot,
    SlotDescriptor,
    Term,
    TernaryMorphism,
    UnaryMorphism,
)


__all__ = [  # noqa: RUF022
    # Args
    "Arg",
    "BoolArg",
    "BytesArg",
    "DictArg",
    "FloatArg",
    "FrozenSetArg",
    "IntArg",
    "ListArg",
    "NoneArg",
    "SetArg",
    "StrArg",
    "TupleArg",
    # Flow
    "Flow",
    "Path",
    "Runtime",
    # Sentinel
    "EMPTY",
    "INVALID",
    "Empty",
    "Invalid",
    "Sentinel",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
    # Term hierarchy
    "Term",
    "LValue",
    "RValue",
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
    # Protocols
    "Gettable",
    "Settable",
    # Context
    "Context",
    # Shape
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]
