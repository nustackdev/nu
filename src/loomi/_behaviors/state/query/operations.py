"""
Operation implementations for the query system.

This module provides various operation types including comparison,
logical, arithmetic, and string operations that can be used in queries.
"""

from __future__ import annotations

import operator
from typing import Any, Callable

from .core import Operation
from .exceptions import OperationNotSupportedError
from .types import EvaluatorProtocol

__all__ = [
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
    # Arithmetic operations
    "AddOperation",
    "SubtractOperation",
    "MultiplyOperation",
    "DivideOperation",
    # String operations
    "ContainsOperation",
    "StartsWithOperation",
    "EndsWithOperation",
    # Unary operations
    "LengthOperation",
    "ExistsOperation",
    # Operation registry
    "OPERATIONS",
    "get_operation",
    "register_operation",
]


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


class ComparisonOperation(Operation):
    """Base class for comparison operations."""

    def _safe_compare(self, left: Any, right: Any, op: Callable[[Any, Any], bool]) -> bool:
        """Safely perform comparison with type checking."""
        try:
            return op(left, right)
        except TypeError:
            # Handle incompatible types gracefully
            return False


class GreaterThanOperation(ComparisonOperation):
    """Greater than comparison: left > right"""

    @property
    def name(self) -> str:
        return "gt"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("gt", type(left))
        return self._safe_compare(left, right, operator.gt)


class LessThanOperation(ComparisonOperation):
    """Less than comparison: left < right"""

    @property
    def name(self) -> str:
        return "lt"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("lt", type(left))
        return self._safe_compare(left, right, operator.lt)


class GreaterEqualOperation(ComparisonOperation):
    """Greater than or equal comparison: left >= right"""

    @property
    def name(self) -> str:
        return "ge"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("ge", type(left))
        return self._safe_compare(left, right, operator.ge)


class LessEqualOperation(ComparisonOperation):
    """Less than or equal comparison: left <= right"""

    @property
    def name(self) -> str:
        return "le"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("le", type(left))
        return self._safe_compare(left, right, operator.le)


class EqualOperation(ComparisonOperation):
    """Equality comparison: left == right"""

    @property
    def name(self) -> str:
        return "eq"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("eq", type(left))
        return left == right


class NotEqualOperation(ComparisonOperation):
    """Not equal comparison: left != right"""

    @property
    def name(self) -> str:
        return "ne"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("ne", type(left))
        return left != right


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


class LogicalOperation(Operation):
    """Base class for logical operations."""

    pass


class AndOperation(LogicalOperation):
    """Logical AND: left and right"""

    @property
    def name(self) -> str:
        return "and"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("and", type(left))
        return bool(left) and bool(right)


class OrOperation(LogicalOperation):
    """Logical OR: left or right"""

    @property
    def name(self) -> str:
        return "or"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("or", type(left))
        return bool(left) or bool(right)


class NotOperation(LogicalOperation):
    """Logical NOT: not left"""

    @property
    def name(self) -> str:
        return "not"

    @property
    def is_unary(self) -> bool:
        return True

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        return not bool(left)


# =============================================================================
# ARITHMETIC OPERATIONS
# =============================================================================


class ArithmeticOperation(Operation):
    """Base class for arithmetic operations."""

    def _safe_arithmetic(self, left: Any, right: Any, op: Callable[[Any, Any], Any]) -> Any:
        """Safely perform arithmetic with type checking."""
        try:
            return op(left, right)
        except TypeError as e:
            raise OperationNotSupportedError(self.name, type(left), type(right)) from e


class AddOperation(ArithmeticOperation):
    """Addition: left + right"""

    @property
    def name(self) -> str:
        return "add"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        if right is None:
            raise OperationNotSupportedError("add", type(left))
        return self._safe_arithmetic(left, right, operator.add)


class SubtractOperation(ArithmeticOperation):
    """Subtraction: left - right"""

    @property
    def name(self) -> str:
        return "sub"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        if right is None:
            raise OperationNotSupportedError("sub", type(left))
        return self._safe_arithmetic(left, right, operator.sub)


class MultiplyOperation(ArithmeticOperation):
    """Multiplication: left * right"""

    @property
    def name(self) -> str:
        return "mul"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        if right is None:
            raise OperationNotSupportedError("mul", type(left))
        return self._safe_arithmetic(left, right, operator.mul)


class DivideOperation(ArithmeticOperation):
    """Division: left / right"""

    @property
    def name(self) -> str:
        return "truediv"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        if right is None:
            raise OperationNotSupportedError("truediv", type(left))
        if right == 0:
            raise ZeroDivisionError("Division by zero")
        return self._safe_arithmetic(left, right, operator.truediv)


# =============================================================================
# STRING OPERATIONS
# =============================================================================


class StringOperation(Operation):
    """Base class for string operations."""

    pass


class ContainsOperation(StringOperation):
    """Contains check: right in left"""

    @property
    def name(self) -> str:
        return "contains"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("contains", type(left))
        try:
            return right in left
        except TypeError:
            return False


class StartsWithOperation(StringOperation):
    """String starts with: left.startswith(right)"""

    @property
    def name(self) -> str:
        return "startswith"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("startswith", type(left))
        try:
            return str(left).startswith(str(right))
        except (TypeError, AttributeError):
            return False


class EndsWithOperation(StringOperation):
    """String ends with: left.endswith(right)"""

    @property
    def name(self) -> str:
        return "endswith"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        if right is None:
            raise OperationNotSupportedError("endswith", type(left))
        try:
            return str(left).endswith(str(right))
        except (TypeError, AttributeError):
            return False


# =============================================================================
# UNARY OPERATIONS
# =============================================================================


class UnaryOperation(Operation):
    """Base class for unary operations."""

    @property
    def is_unary(self) -> bool:
        return True


class LengthOperation(UnaryOperation):
    """Length operation: len(left)"""

    @property
    def name(self) -> str:
        return "length"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> int:
        try:
            return len(left)
        except TypeError as e:
            raise OperationNotSupportedError("length", type(left)) from e


class ExistsOperation(UnaryOperation):
    """Existence check: left is not None"""

    @property
    def name(self) -> str:
        return "exists"

    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> bool:
        return left is not None


# =============================================================================
# OPERATION REGISTRY
# =============================================================================

# Global registry of operations
OPERATIONS: dict[str, Operation] = {
    # Comparison
    "gt": GreaterThanOperation(),
    "lt": LessThanOperation(),
    "ge": GreaterEqualOperation(),
    "le": LessEqualOperation(),
    "eq": EqualOperation(),
    "ne": NotEqualOperation(),
    # Logical
    "and": AndOperation(),
    "or": OrOperation(),
    "not": NotOperation(),
    # Arithmetic
    "add": AddOperation(),
    "sub": SubtractOperation(),
    "mul": MultiplyOperation(),
    "truediv": DivideOperation(),
    # String
    "contains": ContainsOperation(),
    "startswith": StartsWithOperation(),
    "endswith": EndsWithOperation(),
    # Unary
    "length": LengthOperation(),
    "exists": ExistsOperation(),
}


def get_operation(name: str) -> Operation:
    """
    Get operation by name.

    Args:
        name: Operation name

    Returns:
        Operation instance

    Raises:
        KeyError: If operation not found
    """
    return OPERATIONS[name]


def register_operation(operation: Operation) -> None:
    """
    Register a new operation.

    Args:
        operation: Operation instance to register
    """
    OPERATIONS[operation.name] = operation
