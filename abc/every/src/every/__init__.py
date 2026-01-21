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
from .sentinel import (
    EMPTY,
    INVALID,
    NOT_SET,
    Empty,
    Invalid,
    NotSet,
    Sentinel,
    is_empty,
    is_invalid,
    is_notset,
    is_sentinel,
    propagate_special,
)
from .term import (
    BinaryMorphism,
    Command,
    Context,
    Gettable,
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
    "NOT_SET",
    "Empty",
    "Invalid",
    "NotSet",
    "Sentinel",
    "is_empty",
    "is_invalid",
    "is_notset",
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
    # Context
    "Context",
    # Shape
    "Shape",
    "ShapeMeta",
    "Slot",
    "SlotDescriptor",
]
