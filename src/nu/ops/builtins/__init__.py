"""Builtin operations — access, call, attr, conversion, special."""

from .access import AtOp, ContainsOp, LenOp, SliceOp
from .attr import DelAttrOp, GetAttrOp, SetAttrOp
from .call import FuncCall, FuncCallCmd, FuncCallOp, MethodCall, MethodCallCmd, MethodCallOp
from .conversion import ToBoolOp, ToBytesOp, ToFloatOp, ToIntOp, ToListOp, ToSetOp, ToStrOp, ToTupleOp
from .special import IsEmptyOp, IsNaNOp, NotEmptyOp, NotNaNOp
