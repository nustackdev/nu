"""Logical morphisms.

Unary: NotOp, BoolOp
Binary: AndOp, OrOp (with short-circuit evaluation)

AndOp and OrOp override execute() for short-circuit semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import BinaryOperation, Sentinel, UnaryOperation, propagate_special


if TYPE_CHECKING:
    from nu.context import Context


__all__ = [
    "AndOp",
    "BoolOp",
    "NotOp",
    "OrOp",
]


# =============================================================================
# UNARY LOGICAL
# =============================================================================


class NotOp[ResultT](UnaryOperation[ResultT]):
    """Logical NOT: not operand.

    Python's 'not' keyword cannot be overloaded.
    Use .not_() method in trait classes instead.
    """

    def apply(self, operand: object) -> ResultT | Sentinel:
        """Apply."""
        return not operand  # type: ignore


class BoolOp(UnaryOperation[bool]):
    """Boolean conversion: bool(operand)."""

    def apply(self, operand: object) -> bool:
        """Apply."""
        return bool(operand)


# =============================================================================
# BINARY LOGICAL (with short-circuit)
# =============================================================================


class AndOp[ResultT](BinaryOperation[ResultT]):
    """Logical AND: left and right.

    Overrides execute() for short-circuit evaluation:
    if left is falsy, returns left without evaluating right.
    """

    async def execute(self, ctx: Context) -> ResultT | Sentinel:
        """Execute AND with short-circuit evaluation."""
        left_val = await self._children[0].execute(ctx)

        # Handle special values for left
        sp = propagate_special(left_val)
        if sp is not None:
            return sp

        # Short-circuit: if left is falsy, return left
        if not left_val:
            return left_val

        # Evaluate right
        right_val = await self._children[1].execute(ctx)

        # Handle special values for right
        special = propagate_special(right_val)
        if special is not None:
            return special

        return left_val and right_val

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        # Not used - execute() handles everything
        raise NotImplementedError


class OrOp[ResultT](BinaryOperation[ResultT]):
    """Logical OR: left or right.

    Overrides execute() for short-circuit evaluation:
    if left is truthy, returns left without evaluating right.
    """

    async def execute(self, ctx: Context) -> ResultT | Sentinel:
        """Execute OR with short-circuit evaluation."""
        left_val = await self._children[0].execute(ctx)

        # Handle special values for left
        sp = propagate_special(left_val)
        if sp is not None:
            return sp

        # Short-circuit: if left is truthy, return left
        if left_val:
            return left_val

        # Evaluate right
        right_val = await self._children[1].execute(ctx)

        # Handle special values for right
        special = propagate_special(right_val)
        if special is not None:
            return special

        return left_val or right_val

    def apply(self, left: object, right: object) -> ResultT | Sentinel:
        """Apply."""
        # Not used - execute() handles everything
        raise NotImplementedError
