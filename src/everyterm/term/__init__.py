"""Layer 4 - declarative access.

This module provides the core Term abstraction for everyshape:
- Term[T] - base for all executable expressions
- Type[T] - unified typed values (literal or computed)
- LValue/RValue - location vs expression duality
- Ref - typed references to locations
- Arg types - standardized input type aliases
"""

from .args import (
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
from .combiners import all_, and_, any_, coalesce, ifelse, none_, or_
from .comp import (
    BinaryOp,
    Command,
    Computation,
    NAryOp,
    Operation,
    TernaryOp,
    UnaryOp,
)
from .context import Context
from .conversion import computed, literal
from .ref import (
    Ref,
)
from .term import (
    LValue,
    RValue,
    Term,
)
from .type import Type


__all__ = [
    "Arg",
    "BinaryOp",
    "BoolArg",
    "BytesArg",
    "Command",
    "Computation",
    "Context",
    "DictArg",
    "FloatArg",
    "FrozenSetArg",
    "IntArg",
    "LValue",
    "ListArg",
    "NAryOp",
    "NoneArg",
    "Operation",
    "PrimitiveRef",
    "RValue",
    "Ref",
    "SetArg",
    "StrArg",
    "Term",
    "TernaryOp",
    "TupleArg",
    "Type",
    "UnaryOp",
    "ViewRef",
    "all_",
    "and_",
    "any_",
    "coalesce",
    "computed",
    "ifelse",
    "literal",
    "none_",
    "or_",
]
