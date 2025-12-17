"""Ternary operations with graceful special value handling.

This module provides type-safe ternary operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from ..term import Operation


if TYPE_CHECKING:
    from ..context import ContextProtocol
    from ..term import RValue
    from .ergonomics import ErgonomicsMixin

__all__ = [
    "ConditionalOp",
    "TernaryOp",
]

# =============================================================================
# ABSTRACT UNARY OPERATION
# =============================================================================

type OpArgument = RValue | ErgonomicsMixin


class TernaryOp[ResultT, ContextT: ContextProtocol](Operation[ResultT, ContextT], ABC):
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
        self.children = (cast("RValue", first), cast("RValue", second), cast("RValue", third))

    @abstractmethod
    def execute(self, context: ContextT) -> ResultT:
        """Execute ternary operation.

        Args:
            context: Execution context

        Returns:
            Operation result or SpecialValue
        """
        ...

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.children!r})"


# =============================================================================
# OPERATIONS
# =============================================================================


class ConditionalOp[ResultT, ContextT: ContextProtocol](TernaryOp[ResultT, ContextT]):
    """Conditional ternary up: a concise, single-op way to perform an if-else check and return a value based on the result."""

    def _apply_op(self, first: object, second: object, third: object) -> ResultT:
        return first if second else third  # type: ignore

    def execute(self, context: ContextT) -> ResultT:
        """Execute conditional operation.

        Args:
            context: Execution context

        Returns:
            Operation result or SpecialValue
        """
        second_val = self.children[1].execute(context)

        if second_val:
            return self.children[0].execute(context)
        else:
            return self.children[2].execute(context)
