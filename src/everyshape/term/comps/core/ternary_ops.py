"""Ternary operations with graceful special value handling.

This module provides type-safe ternary operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from ...term import Operation


if TYPE_CHECKING:
    from ...context import Context
    from ...term import Term
    from ...types.bases import UnionBaseType


__all__ = [
    "ConditionalOp",
    "TernaryOp",
]

# =============================================================================
# ABSTRACT UNARY OPERATION
# =============================================================================


type OpArgument = Term | UnionBaseType


class TernaryOp[ResultT](Operation[ResultT], ABC):
    """Base class for ternary operations.

    Defines execution pattern: evaluate operand → handle special values →
    apply operator → return result.

    Subclasses implement specific operators (ConditionalOp, etc.).
    """

    def __init__(self, first: OpArgument, second: OpArgument, third: OpArgument) -> None:
        """Initialize unary operation.

        Args:
            op: Operator name
            first: First operand
            second: Second operand
            third: Third operand
        """
        self.children = (cast("Term", first), cast("Term", second), cast("Term", third))

    @abstractmethod
    def execute(self, context: Context) -> ResultT:
        """Execute ternary operation.

        Args:
            context: Execution context

        Returns:
            Operation result or Sentinel
        """
        ...

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children!r})"


# =============================================================================
# OPERATIONS
# =============================================================================


class ConditionalOp[ResultT](TernaryOp[ResultT]):
    """Conditional ternary up: a concise, single-op way to perform an if-else check and return a value based on the result."""

    def _apply_op(self, first: object, second: object, third: object) -> ResultT:
        return first if second else third  # type: ignore

    def execute(self, context: Context) -> ResultT:
        """Execute conditional operation.

        Args:
            context: Execution context

        Returns:
            Operation result or Sentinel
        """
        second_val = self.children[1].execute(context)

        if second_val:
            return self.children[0].execute(context)
        else:
            return self.children[2].execute(context)
