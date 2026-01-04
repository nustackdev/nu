"""Foundation tier: Arity-based computation base classes.

This module provides centralized access to the base computation classes
organized by operand count (arity):

- UnaryOp: Single operand operations (NegOp, AbsOp, NotOp, etc.)
- BinaryOp: Two operand operations (AddOp, SubOp, GtOp, etc.)
- TernaryOp: Three operand operations (ConditionalOp, etc.)

All bases inherit from Operation (which extends Computation from term.py)
and provide:
- children tuple: Stores operands for tree traversal
- execute(): Evaluates operands and applies operation
- _apply_op(): Abstract method for subclass implementation

Usage:
    from everyshape.term.comps.bases import UnaryOp, BinaryOp, TernaryOp

    class MyCustomOp(UnaryOp[int]):
        def _apply_op(self, operand: object) -> int:
            return int(operand) * 2
"""

from ..value.binary_ops import BinaryOp
from ..value.ternary_ops import TernaryOp
from ..value.unary_ops import UnaryOp


__all__ = [
    "BinaryOp",
    "TernaryOp",
    "UnaryOp",
]
