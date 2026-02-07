"""everybase.core — Computation layer.

Packages:
    term/     -- computation (Term, Ref, Morphism, Sentinel)
    flow/     -- ordering (Flow)
    span/     -- grouping (Span)
    context/  -- runtime (Context, Handle)
    exec      -- Executable base
"""

from __future__ import annotations

from ..tree import Node
from .context import Context, Handle
from .executable import Executable
from .flow import Flow
from .model import Model
from .span import Span
from .term import (
    EMPTY,
    INVALID,
    Arg,
    BinaryCommand,
    BinaryMorphism,
    BinaryOperation,
    BoolArg,
    BytesArg,
    Command,
    DictArg,
    Empty,
    FloatArg,
    FrozenSetArg,
    IntArg,
    Invalid,
    ListArg,
    LValue,
    Morphism,
    NAryCommand,
    NAryMorphism,
    NAryOperation,
    NoneArg,
    Operation,
    Ref,
    RValue,
    Sentinel,
    SetArg,
    StrArg,
    Term,
    TernaryCommand,
    TernaryMorphism,
    TernaryOperation,
    TupleArg,
    UnaryCommand,
    UnaryMorphism,
    UnaryOperation,
    Value,
    is_empty,
    is_invalid,
    is_sentinel,
    propagate_special,
)


__all__ = [  # noqa: RUF022
    # Tree
    "Node",
    "Executable",
    # Term
    "Term",
    "LValue",
    "RValue",
    "Value",
    "Ref",
    "Morphism",
    "NAryMorphism",
    "UnaryMorphism",
    "BinaryMorphism",
    "TernaryMorphism",
    "Operation",
    "Command",
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
    # Model
    "Model",
    # Flow & Span
    "Flow",
    "Span",
    # Context
    "Context",
    "Handle",
]
