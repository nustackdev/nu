"""
Operation implementations for the query system.

This module provides the operation hierarchy with base classes and concrete
implementations. Operations are immutable and contain their operands, with
a single calc() method that performs the computation.
"""

from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import attrs

if TYPE_CHECKING:
    from ..path import Path
    from ..tree import Tree
    from .evaluator import QueryEvaluator

__all__ = [
    # Base classes
    "Operation",
    "UnaryOperation",
    "BinaryOperation",
    "TernaryOperation",
    # Path resolution
    "ResolveVarOperation",
    # Arithmetic operations
    "AddOperation",
    "SubtractOperation",
    "MultiplyOperation",
    "DivideOperation",
    # Comparison operations
    "GreaterThanOperation",
    "LessThanOperation",
    "GreaterEqualOperation",
    "LessEqualOperation",
    "EqualOperation",
    "NotEqualOperation",
    # Logical operations
    "AndOperation",
    "OrOperation",
    "NotOperation",
    # String operations
    "ContainsOperation",
    "StartsWithOperation",
    "EndsWithOperation",
    # Function operations
    "LengthOperation",
    "MaxOperation",
    "MinOperation",
    "SumOperation",
]


# =============================================================================
# BASE OPERATION CLASSES
# =============================================================================


@attrs.define(frozen=True)
class Operation(ABC):
    """
    Base class for all operations.

    Operations are immutable objects that contain their operands and provide
    a single calc() method to perform the computation. They form the nodes
    of the operation tree that represents a query.
    """

    @abstractmethod
    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """
        Calculate and return the result of this operation.

        Args:
            evaluator: QueryEvaluator for resolving nested operations
            tree: Tree instance for data access
            ctx: Optional context (transaction/snapshot)

        Returns:
            Result of the operation
        """
        pass


@attrs.define(frozen=True)
class UnaryOperation(Operation, ABC):
    """
    Base class for operations with a single operand.

    Unary operations operate on a single value, such as length(), max(), min(), etc.
    """

    operand: Operation | Any = attrs.field()

    def _resolve_operand(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Resolve the operand to its value."""
        return evaluator.resolve_operand(self.operand, tree, ctx)


@attrs.define(frozen=True)
class BinaryOperation(Operation, ABC):
    """
    Base class for operations with two operands.

    Binary operations operate on two values, such as addition, comparison, etc.
    """

    left: Operation | Any = attrs.field()
    right: Operation | Any = attrs.field()

    def _resolve_operands(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> tuple[Any, Any]:
        """Resolve both operands to their values."""
        left_val = evaluator.resolve_operand(self.left, tree, ctx)
        right_val = evaluator.resolve_operand(self.right, tree, ctx)
        return left_val, right_val


@attrs.define(frozen=True)
class TernaryOperation(Operation, ABC):
    """
    Base class for operations with three operands.

    Ternary operations operate on three values, such as conditional expressions.
    """

    first: Operation | Any = attrs.field()
    second: Operation | Any = attrs.field()
    third: Operation | Any = attrs.field()

    def _resolve_operands(
        self, evaluator: QueryEvaluator, tree: Tree, ctx: Any
    ) -> tuple[Any, Any, Any]:
        """Resolve all three operands to their values."""
        first_val = evaluator.resolve_operand(self.first, tree, ctx)
        second_val = evaluator.resolve_operand(self.second, tree, ctx)
        third_val = evaluator.resolve_operand(self.third, tree, ctx)
        return first_val, second_val, third_val


# =============================================================================
# PATH RESOLUTION OPERATION
# =============================================================================


@attrs.define(frozen=True)
class ResolveVarOperation(UnaryOperation):
    """
    Operation that resolves a path to its value in the tree.

    This operation wraps path resolution for consistency - everything in the
    query system is an operation. It uses PathResolver to get the actual value.
    """

    operand: Path = attrs.field()

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """
        Resolve the path to its value in the tree.

        Args:
            evaluator: QueryEvaluator instance
            tree: Tree to resolve path against
            ctx: Optional context

        Returns:
            Value at the path location
        """
        return evaluator.resolve_path(self.operand, tree, ctx)

    def __repr__(self) -> str:
        return f"ResolveVar({self.operand})"


# =============================================================================
# ARITHMETIC OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class AddOperation(BinaryOperation):
    """Addition operation: left + right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Perform addition of two operands."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return operator.add(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot add {type(left_val).__name__} and {type(right_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class SubtractOperation(BinaryOperation):
    """Subtraction operation: left - right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Perform subtraction of two operands."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return operator.sub(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot subtract {type(right_val).__name__} from {type(left_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class MultiplyOperation(BinaryOperation):
    """Multiplication operation: left * right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Perform multiplication of two operands."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return operator.mul(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot multiply {type(left_val).__name__} and {type(right_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class DivideOperation(BinaryOperation):
    """Division operation: left / right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Perform division of two operands."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            if right_val == 0:
                raise ZeroDivisionError("Division by zero")
            return operator.truediv(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot divide {type(left_val).__name__} by {type(right_val).__name__}"
            ) from e


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class GreaterThanOperation(BinaryOperation):
    """Greater than operation: left > right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform greater than comparison."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return operator.gt(left_val, right_val)
        except TypeError:
            # Handle incomparable types gracefully
            return False


@attrs.define(frozen=True)
class LessThanOperation(BinaryOperation):
    """Less than operation: left < right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform less than comparison."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return operator.lt(left_val, right_val)
        except TypeError:
            return False


@attrs.define(frozen=True)
class GreaterEqualOperation(BinaryOperation):
    """Greater than or equal operation: left >= right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform greater than or equal comparison."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return operator.ge(left_val, right_val)
        except TypeError:
            return False


@attrs.define(frozen=True)
class LessEqualOperation(BinaryOperation):
    """Less than or equal operation: left <= right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform less than or equal comparison."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return operator.le(left_val, right_val)
        except TypeError:
            return False


@attrs.define(frozen=True)
class EqualOperation(BinaryOperation):
    """Equality operation: left == right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform equality comparison."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        return left_val == right_val


@attrs.define(frozen=True)
class NotEqualOperation(BinaryOperation):
    """Not equal operation: left != right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform not equal comparison."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        return left_val != right_val


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class AndOperation(BinaryOperation):
    """Logical AND operation: left and right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform logical AND with short-circuit evaluation."""
        left_val = evaluator.resolve_operand(self.left, tree, ctx)
        if not left_val:
            return False  # Short-circuit
        right_val = evaluator.resolve_operand(self.right, tree, ctx)
        return bool(left_val) and bool(right_val)


@attrs.define(frozen=True)
class OrOperation(BinaryOperation):
    """Logical OR operation: left or right"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform logical OR with short-circuit evaluation."""
        left_val = evaluator.resolve_operand(self.left, tree, ctx)
        if left_val:
            return True  # Short-circuit
        right_val = evaluator.resolve_operand(self.right, tree, ctx)
        return bool(left_val) or bool(right_val)


@attrs.define(frozen=True)
class NotOperation(UnaryOperation):
    """Logical NOT operation: not operand"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Perform logical NOT."""
        operand_val = self._resolve_operand(evaluator, tree, ctx)
        return not bool(operand_val)


# =============================================================================
# STRING OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class ContainsOperation(BinaryOperation):
    """Contains operation: right in left"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Check if right operand is contained in left operand."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return right_val in left_val
        except TypeError:
            return False


@attrs.define(frozen=True)
class StartsWithOperation(BinaryOperation):
    """String starts with operation: left.startswith(right)"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Check if left operand starts with right operand."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return str(left_val).startswith(str(right_val))
        except (TypeError, AttributeError):
            return False


@attrs.define(frozen=True)
class EndsWithOperation(BinaryOperation):
    """String ends with operation: left.endswith(right)"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> bool:
        """Check if left operand ends with right operand."""
        left_val, right_val = self._resolve_operands(evaluator, tree, ctx)
        try:
            return str(left_val).endswith(str(right_val))
        except (TypeError, AttributeError):
            return False


# =============================================================================
# FUNCTION OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class LengthOperation(UnaryOperation):
    """Length operation: len(operand)"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> int:
        """Get length of operand."""
        operand_val = self._resolve_operand(evaluator, tree, ctx)
        try:
            return len(operand_val)
        except TypeError as e:
            raise ValueError(f"Cannot get length of {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class MaxOperation(UnaryOperation):
    """Maximum operation: max(operand)"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Get maximum value from operand."""
        operand_val = self._resolve_operand(evaluator, tree, ctx)
        try:
            return max(operand_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot get max of {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class MinOperation(UnaryOperation):
    """Minimum operation: min(operand)"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Get minimum value from operand."""
        operand_val = self._resolve_operand(evaluator, tree, ctx)
        try:
            return min(operand_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot get min of {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class SumOperation(UnaryOperation):
    """Sum operation: sum(operand)"""

    def calc(self, evaluator: QueryEvaluator, tree: Tree, ctx: Any) -> Any:
        """Get sum of operand values."""
        operand_val = self._resolve_operand(evaluator, tree, ctx)
        try:
            return sum(operand_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot get sum of {type(operand_val).__name__}") from e
