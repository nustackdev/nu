"""Logical morphisms.

Unary: NotOp, BoolOp
Binary: AndOp, OrOp (with short-circuit evaluation)

AndOp and OrOp override execute() for short-circuit semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import BinaryMorphism, Operation, Sentinel, UnaryMorphism, propagate_special


if TYPE_CHECKING:
    from everyabc import Context


__all__ = [
    "AndOp",
    "BoolOp",
    "NotOp",
    "OrOp",
]


# =============================================================================
# UNARY LOGICAL
# =============================================================================


class NotOp[ResultT](Operation, UnaryMorphism[ResultT | Sentinel]):
    """Logical NOT: not operand.

    Python's 'not' keyword cannot be overloaded.
    Use .not_() method in trait classes instead.
    """

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        return not operand  # type: ignore


class BoolOp(Operation, UnaryMorphism[bool]):
    """Boolean conversion: bool(operand)."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return bool(operand)


# =============================================================================
# BINARY LOGICAL (with short-circuit)
# =============================================================================


class AndOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Logical AND: left and right.

    Overrides execute() for short-circuit evaluation:
    if left is falsy, returns left without evaluating right.
    """

    def execute(self, ctx: Context) -> ResultT | Sentinel:
        """Execute AND with short-circuit evaluation."""
        left_val = self._resolve(self._children[0], ctx)

        # Handle special values for left
        sp = propagate_special(left_val)
        if sp is not None:
            return sp

        # Short-circuit: if left is falsy, return left
        if not left_val:
            return left_val

        # Evaluate right
        right_val = self._resolve(self._children[1], ctx)

        # Handle special values for right
        special = propagate_special(right_val)
        if special is not None:
            return special

        return left_val and right_val

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        # Not used - execute() handles everything
        raise NotImplementedError


class OrOp[ResultT](Operation, BinaryMorphism[ResultT]):
    """Logical OR: left or right.

    Overrides execute() for short-circuit evaluation:
    if left is truthy, returns left without evaluating right.
    """

    def execute(self, ctx: Context) -> ResultT | Sentinel:
        """Execute OR with short-circuit evaluation."""
        left_val = self._resolve(self._children[0], ctx)

        # Handle special values for left
        sp = propagate_special(left_val)
        if sp is not None:
            return sp

        # Short-circuit: if left is truthy, return left
        if left_val:
            return left_val  # type: ignore[return-value]

        # Evaluate right
        right_val = self._resolve(self._children[1], ctx)

        # Handle special values for right
        special = propagate_special(right_val)
        if special is not None:
            return special  # type: ignore[return-value]

        return left_val or right_val  # type: ignore[return-value]

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        # Not used - execute() handles everything
        raise NotImplementedError
