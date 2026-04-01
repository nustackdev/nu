"""Nu terms - building blocks of the algebra."""

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
from .nu import LValue, Nu, RValue
from .op import (
    BinaryCalc,
    BinaryCmd,
    BinaryOp,
    Calculation,
    Command,
    NAryCalc,
    NAryCmd,
    NAryOp,
    Op,
    TernaryCalc,
    TernaryCmd,
    TernaryOp,
    UnaryCalc,
    UnaryCmd,
    UnaryOp,
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
from .span import Span
from .value import Value


__all__ = [
    # Core
    "Nu",
    "LValue",
    "RValue",
    # Terms
    "Value",
    "Ref",
    "Op",
    "NAryOp",
    "UnaryOp",
    "BinaryOp",
    "TernaryOp",
    "Span",
    # Purity
    "Calculation",
    "Command",
    # Convenience: purity + arity
    "NAryCalc",
    "NAryCmd",
    "UnaryCalc",
    "UnaryCmd",
    "BinaryCalc",
    "BinaryCmd",
    "TernaryCalc",
    "TernaryCmd",
    # Sentinels
    "Sentinel",
    "Empty",
    "Invalid",
    "EMPTY",
    "INVALID",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
    # Args
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
