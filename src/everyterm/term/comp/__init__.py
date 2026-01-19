"""Computation defition, and arity base classes for operations.

This module provides the 4 fundamental arity bases that all operations inherit from:

- UnaryOp[T]: Single operand operations (neg, abs, not, etc.)
- BinaryOp[T]: Two operand operations (add, sub, mul, gt, eq, etc.)
- TernaryOp[T]: Three operand operations (conditional, slice, etc.)
- NAryOp[T]: Variable argument operations (func calls, method calls, etc.)

All leaf operations inherit from one of these bases and implement `_apply_op()`.
The base handles `execute()` boilerplate (operand evaluation, special value propagation).
Override `execute()` only when needed (e.g., short-circuit in AndOp/OrOp).
"""

from .binary import BinaryOp
from .comp import Command, Computation, Operation
from .nary import NAryOp
from .ternary import TernaryOp
from .unary import UnaryOp


__all__ = [
    "BinaryOp",
    "Command",
    "Computation",
    "NAryOp",
    "Operation",
    "TernaryOp",
    "UnaryOp",
]
