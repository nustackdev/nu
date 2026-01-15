"""Base class for N-ary operations.

N-ary operations have variable numbers of arguments, used for:
- Operations with optional parameters: SplitOp, StripOp, FindOp, etc.
- Function calls: FuncCallOp, MethodCallOp
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ..conversion import literal
from .comp import Operation


if TYPE_CHECKING:
    from ..context import Context

__all__ = ["NAryOp"]


class NAryOp[ResultT](Operation[ResultT], ABC):
    """Base class for N-ary operations (variable arguments).

    Defines execution pattern:
    1. Evaluate all operands
    2. Apply operation via `_apply_op()`
    3. Return result

    Subclasses implement `_apply_op()` with operation-specific logic.
    Override `__init__` to store extra config (callables, flags, etc.).
    Override `execute()` only for special handling (lazy evaluation, etc.).

    Example simple case:
        class SplitOp(NAryOp[list[str]]):
            def _apply_op(self, operand, sep, maxsplit) -> list[str]:
                return operand.split(sep, int(maxsplit))

    Example with config:
        class MapOp(NAryOp[list]):
            def __init__(self, operand, fn):
                super().__init__(operand)  # Just operand as child
                self._fn = fn  # Callable stored separately

            def _apply_op(self, operand) -> list:
                return list(map(self._fn, operand))
    """

    def __init__(self, *operands: object) -> None:
        """Initialize N-ary operation.

        Args:
            *operands: Operands (can be Terms or literal values)
        """
        self.children = tuple(literal(op) for op in operands)

    def execute(self, context: Context) -> ResultT:
        """Execute N-ary operation.

        Evaluates all operands and applies operation logic.

        Args:
            context: Execution context

        Returns:
            Operation result
        """
        resolved = tuple(child.execute(context) for child in self.children)
        return self._apply_op(*resolved)

    @abstractmethod
    def _apply_op(self, *args: Any, **kwargs: Any) -> ResultT:  # noqa: ANN401
        """Apply the operator to operands.

        Subclasses override with operation-specific logic.s

        Args:
            *args: Evaluated operand args
            **kwargs: Evaluated operand kwargs

        Returns:
            Operation result
        """
        raise NotImplementedError()

    def __repr__(self) -> str:
        """String representation."""
        args = ", ".join(repr(c) for c in self.children)
        return f"{self.__class__.__name__}({args})"
