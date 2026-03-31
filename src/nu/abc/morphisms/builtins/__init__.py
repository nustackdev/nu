"""Python builtin morphisms — type conversion, access, attribute, callable invocation, sentinel checks."""

from .access import AtOp, ContainsOp, LenOp, SliceOp
from .attr import DelAttrOp, GetAttrOp, SetAttrOp
from .call import FuncCall, FuncCallCmd, FuncCallOp, MethodCall, MethodCallCmd, MethodCallOp
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
from .special import IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp


__all__ = [
    "AtOp",
    "ContainsOp",
    "DelAttrOp",
    "FuncCall",
    "FuncCallCmd",
    "FuncCallOp",
    "GetAttrOp",
    "IsEmptyOp",
    "IsNaNOp",
    "LenOp",
    "MethodCall",
    "MethodCallCmd",
    "MethodCallOp",
    "NotEmptyOp",
    "NotNaNOp",
    "SetAttrOp",
    "SliceOp",
    "ToBoolOp",
    "ToBytesOp",
    "ToFloatOp",
    "ToIntOp",
    "ToListOp",
    "ToSetOp",
    "ToStrOp",
    "ToTupleOp",
]
