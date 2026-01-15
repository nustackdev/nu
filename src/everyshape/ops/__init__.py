"""Computations module - operations organized by arity and category.

Structure:
- base/: 4 fundamental arity bases (UnaryOp, BinaryOp, TernaryOp, NAryOp)
- arithmetic.py: NegOp, AbsOp, PosOp, AddOp, SubOp, MulOp, DivOp, etc.
- comparison.py: EqOp, NeOp, GtOp, LtOp, GeOp, LeOp, IdCompOp
- logical.py: NotOp, BoolOp, AndOp, OrOp
- bitwise.py: BitwiseNotOp, BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp
- conversion.py: ToIntOp, ToStrOp, ToBoolOp, ToFloatOp, ToBytesOp, etc.
- special.py: IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp
- conditional.py: ConditionalOp
- callable_.py: FuncCallOp, MethodCallOp, GetAttrOp, SetAttrOp, DelAttrOp
- collection/: Generic collection ops (AtOp, LenOp, MapOp, FilterOp, etc.)

All leaf ops inherit from one of 4 arity bases and implement `_apply_op()`.
"""

# Arity bases
# Arithmetic
from .arithmetic import (
    AbsOp,
    AddOp,
    DivOp,
    FloorDivOp,
    ModOp,
    MulOp,
    NegOp,
    PosOp,
    PowOp,
    SubOp,
)

# Bitwise
from .bitwise import (
    BitwiseAndOp,
    BitwiseNotOp,
    BitwiseOrOp,
    LShiftOp,
    RShiftOp,
    XorOp,
)

# Callable (function/method invocation)
from .callable import DelAttrOp, FuncCallOp, GetAttrOp, MethodCallOp, SetAttrOp

# Collection ops
from .collection import (
    AllOp,
    AnyOp,
    AtOp,
    ContainsOp,
    CountOp,
    FilterOp,
    FindIndexOp,
    FindOp,
    FirstOp,
    IndexOfOp,
    JoinOp,
    LastOp,
    LenOp,
    MapOp,
    MaxOp,
    MinOp,
    ReduceOp,
    ReversedOp,
    SliceOp,
    SortedOp,
    SumOp,
)

# Comparison
from .comparison import EqOp, GeOp, GtOp, IdCompOp, LeOp, LtOp, NeOp

# Conditional
from .conditional import ConditionalOp

# Conversion
from .conversion import (
    ToBoolOp,
    ToBytesOp,
    ToFloatOp,
    ToIntOp,
    ToListOp,
    ToSetOp,
    ToStrOp,
    ToTupleOp,
)
from .core import BinaryOp, NAryOp, TernaryOp, UnaryOp

# Logical
from .logical import AndOp, BoolOp, NotOp, OrOp

# Special value checks
from .special import IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp


__all__ = [  # noqa: RUF022
    # Arity bases
    "BinaryOp",
    "NAryOp",
    "TernaryOp",
    "UnaryOp",
    # Arithmetic
    "AbsOp",
    "AddOp",
    "DivOp",
    "FloorDivOp",
    "ModOp",
    "MulOp",
    "NegOp",
    "PosOp",
    "PowOp",
    "SubOp",
    # Comparison
    "EqOp",
    "GeOp",
    "GtOp",
    "IdCompOp",
    "LeOp",
    "LtOp",
    "NeOp",
    # Logical
    "AndOp",
    "BoolOp",
    "NotOp",
    "OrOp",
    # Bitwise
    "BitwiseAndOp",
    "BitwiseNotOp",
    "BitwiseOrOp",
    "LShiftOp",
    "RShiftOp",
    "XorOp",
    # Conversion
    "ToBoolOp",
    "ToBytesOp",
    "ToFloatOp",
    "ToIntOp",
    "ToListOp",
    "ToSetOp",
    "ToStrOp",
    "ToTupleOp",
    # Special
    "IsEmptyOp",
    "IsNaNOp",
    "NotEmptyOp",
    "NotNaNOp",
    # Conditional
    "ConditionalOp",
    # Callable
    "DelAttrOp",
    "FuncCallOp",
    "GetAttrOp",
    "MethodCallOp",
    "SetAttrOp",
    # Collection
    "AllOp",
    "AnyOp",
    "AtOp",
    "ContainsOp",
    "CountOp",
    "FilterOp",
    "FindIndexOp",
    "FindOp",
    "FirstOp",
    "IndexOfOp",
    "JoinOp",
    "LastOp",
    "LenOp",
    "MapOp",
    "MaxOp",
    "MinOp",
    "ReduceOp",
    "ReversedOp",
    "SliceOp",
    "SortedOp",
    "SumOp",
]
