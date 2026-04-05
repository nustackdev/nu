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
from .type_vars import T_co
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
    "EMPTY",
    "INVALID",
    # Args
    "Arg",
    "BinaryCalc",
    "BinaryCmd",
    "BinaryOp",
    "BoolArg",
    "BytesArg",
    # Purity
    "Calculation",
    "Command",
    "DictArg",
    "Empty",
    "FloatArg",
    "FrozenSetArg",
    "IntArg",
    "Invalid",
    "LValue",
    "ListArg",
    # Convenience: purity + arity
    "NAryCalc",
    "NAryCmd",
    "NAryOp",
    "NoneArg",
    # Core
    "Nu",
    "Op",
    "RValue",
    "Ref",
    # Sentinels
    "Sentinel",
    "SetArg",
    "Span",
    "StrArg",
    "TernaryCalc",
    "TernaryCmd",
    "TernaryOp",
    "T_co",
    "TupleArg",
    "UnaryCalc",
    "UnaryCmd",
    "UnaryOp",
    # Terms
    "Value",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
]
