"""Scalar queries - single-value functional construction."""

from .access import At, Contains, Len, Slice
from .arithmetic import (
    Abs,
    Add,
    Div,
    FloorDiv,
    Mod,
    Mul,
    Neg,
    Pos,
    Pow,
    Sub,
)
from .attr import DelAttr, GetAttr, SetAttr
from .bitwise import (
    BitwiseAnd,
    BitwiseNot,
    BitwiseOr,
    LShift,
    RShift,
    Xor,
)
from .combine import Chain, Enumerate, Zip
from .combiners import all_, and_, any_, none_, or_
from .comparison import (
    Eq,
    Ge,
    Gt,
    IdComp,
    Le,
    Lt,
    Ne,
)
from .control import If, Switch
from .conversion import (
    ToBool,
    ToBytes,
    ToFloat,
    ToInt,
    ToList,
    ToSet,
    ToStr,
    ToTuple,
)
from .iter_reduce import Find, FindIndex, GroupBy, Partition, ToDict
from .logical import (
    And,
    Bool,
    Not,
    Or,
)
from .reduce import AllElem, AnyElem, MaxElem, MinElem, Sum
from .sentinel import IsEmpty, IsInvalid, NotEmpty, NotInvalid
from .slice import Drop, Take
from .timing import Timed
from .transform import (
    FilterBy,
    Flatten,
    Pluck,
    Reversed,
    Sorted,
    Unique,
)


__all__ = [
    "Abs",
    "Add",
    "AllElem",
    "And",
    "AnyElem",
    "At",
    "BitwiseAnd",
    "BitwiseNot",
    "BitwiseOr",
    "Bool",
    "Chain",
    "Contains",
    "DelAttr",
    "Div",
    "Drop",
    "Enumerate",
    "Eq",
    "FilterBy",
    "Find",
    "FindIndex",
    "Flatten",
    "FloorDiv",
    "Ge",
    "GetAttr",
    "GroupBy",
    "Gt",
    "IdComp",
    "If",
    "IsEmpty",
    "IsInvalid",
    "LShift",
    "Le",
    "Len",
    "Lt",
    "MaxElem",
    "MinElem",
    "Mod",
    "Mul",
    "Ne",
    "Neg",
    "Not",
    "NotEmpty",
    "NotInvalid",
    "Or",
    "Partition",
    "Pluck",
    "Pos",
    "Pow",
    "RShift",
    "Reversed",
    "SetAttr",
    "Slice",
    "Sorted",
    "Sub",
    "Sum",
    "Switch",
    "Take",
    "Timed",
    "ToBool",
    "ToBytes",
    "ToDict",
    "ToFloat",
    "ToInt",
    "ToList",
    "ToSet",
    "ToStr",
    "ToTuple",
    "Unique",
    "Xor",
    "Zip",
    "all_",
    "and_",
    "any_",
    "none_",
    "or_",
]
