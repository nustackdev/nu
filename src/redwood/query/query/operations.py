"""Operation implementations for the query system.

This module provides the operation hierarchy with base classes and concrete
implementations. Operations are immutable and contain their operands, with
a single calc() method that performs the computation.
"""

from __future__ import annotations

import operator
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import attrs

from .exceptions import QueryEvaluationError


if TYPE_CHECKING:
    from redwood.tree import Tree

    from ..path import _Path

__all__ = [
    "AbsOperation",
    # Arithmetic operations
    "AddOperation",
    # Logical operations
    "AndOperation",
    "AnyOperation",
    "BinaryOperation",
    "BoolOperation",
    # String operations
    "ContainsOperation",
    "CountOperation",
    "DivideOperation",
    "EndsWithOperation",
    "EqualOperation",
    "EveryOperation",
    "GreaterEqualOperation",
    # Comparison operations
    "GreaterThanOperation",
    # Function operations
    "LengthOperation",
    "LessEqualOperation",
    "LessThanOperation",
    "MaxOperation",
    "MinOperation",
    "ModuloOperation",
    "MultiplyOperation",
    "NotEqualOperation",
    "NotOperation",
    # Base classes
    "Operation",
    "OrOperation",
    "PowerOperation",
    # Path resolution
    "ResolveVarOperation",
    "StartsWithOperation",
    "SubtractOperation",
    "SumOperation",
    "TernaryOperation",
    "UnaryOperation",
]


# =============================================================================
# BASE OPERATION CLASSES
# =============================================================================


@attrs.define(frozen=True)
class Operation(ABC):
    """Base class for all operations.

    Operations are immutable objects that contain their operands and provide
    a single calc() method to perform the computation. They form the nodes
    of the operation tree that represents a query.
    """

    @staticmethod
    def s__resolve_operand(
        operand: Operation | Any, tree: Tree, ctx: Any, vars: dict[str | int, Any]
    ) -> Any:
        """Resolve an operand to its actual value.

        Operands can be either nested operations (which need to be calculated)
        or literal values (which are returned as-is). This method handles
        the distinction and ensures proper evaluation.

        Args:
            operand: Operand to resolve - either an Operation or literal value
            tree: Tree instance for data access
            ctx: Optional context for operations

        Returns:
            Resolved value of the operand

        Raises:
            QueryEvaluationError: If operand resolution fails

        Example:
            ```python
            # Resolve nested operation
            result = evaluator.resolve_operand(add_operation, tree)

            # Resolve literal value
            result = evaluator.resolve_operand(42, tree)  # Returns 42
            ```
        """
        try:
            if isinstance(operand, Operation):
                # Operand is a nested operation - calculate it
                return operand.calc(tree, ctx, vars)
            else:
                # Operand is a literal value - return as-is
                return operand
        except Exception as e:
            if isinstance(e, QueryEvaluationError):
                raise
            raise QueryEvaluationError(
                f"Failed to resolve operand: {operand}", original_error=e
            ) from e

    @staticmethod
    def s__resolve_path(path: _Path, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Resolve a path to its value in the tree.

        This method uses the PathResolver to navigate through the tree
        structure and retrieve the actual value at the specified path.
        It serves as the bridge between the query system and path resolution.

        Args:
            path: Path object to resolve
            tree: Tree instance to resolve path against
            ctx: Optional context for path resolution

        Returns:
            Value at the path location in the tree

        Raises:
            QueryEvaluationError: If path resolution fails

        Example:
            ```python
            # Resolve path to actual value
            email = evaluator.resolve_path(email_path, tree)

            # Resolve with transaction context
            with tree.transaction() as tx:
                value = evaluator.resolve_path(config_path, tree, ctx=tx, vars=vars)
            ```
        """
        try:
            return path.resolve(tree, ctx, vars)
        except Exception as e:
            raise QueryEvaluationError(f"Failed to resolve path: {path}", original_error=e) from e

    @abstractmethod
    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Calculate and return the result of this operation.

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
    """Base class for operations with a single operand.

    Unary operations operate on a single value, such as length(), max(), min(), etc.
    """

    operand: Operation | Any = attrs.field()

    def _resolve_operand(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Resolve the operand to its value."""
        return self.s__resolve_operand(self.operand, tree, ctx, vars)


@attrs.define(frozen=True)
class BinaryOperation(Operation, ABC):
    """Base class for operations with two operands.

    Binary operations operate on two values, such as addition, comparison, etc.
    """

    left: Operation | Any = attrs.field()
    right: Operation | Any = attrs.field()

    def _resolve_operands(
        self, tree: Tree, ctx: Any, vars: dict[str | int, Any]
    ) -> tuple[Any, Any]:
        """Resolve both operands to their values."""
        left_val = self.s__resolve_operand(self.left, tree, ctx, vars)
        right_val = self.s__resolve_operand(self.right, tree, ctx, vars)
        return left_val, right_val


@attrs.define(frozen=True)
class TernaryOperation(Operation, ABC):
    """Base class for operations with three operands.

    Ternary operations operate on three values, such as conditional expressions.
    """

    first: Operation | Any = attrs.field()
    second: Operation | Any = attrs.field()
    third: Operation | Any = attrs.field()

    def _resolve_operands(
        self, tree: Tree, ctx: Any, vars: dict[str | int, Any]
    ) -> tuple[Any, Any, Any]:
        """Resolve all three operands to their values."""
        first_val = self.s__resolve_operand(self.first, tree, ctx, vars)
        second_val = self.s__resolve_operand(self.second, tree, ctx, vars)
        third_val = self.s__resolve_operand(self.third, tree, ctx, vars)
        return first_val, second_val, third_val


# =============================================================================
# PATH RESOLUTION OPERATION
# =============================================================================


@attrs.define(frozen=True)
class ResolveVarOperation(UnaryOperation):
    """Operation that resolves a path to its value in the tree.

    This operation wraps path resolution for consistency - everything in the
    query system is an operation. It uses PathResolver to get the actual value.
    """

    operand: _Path = attrs.field()

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Resolve the path to its value in the tree.

        Args:
            evaluator: QueryEvaluator instance
            tree: Tree to resolve path against
            ctx: Optional context

        Returns:
            Value at the path location
        """
        return self.s__resolve_path(self.operand, tree, ctx, vars)

    def __repr__(self) -> str:
        return f"ResolveVar({self.operand})"


# =============================================================================
# ARITHMETIC OPERATIONS
# =============================================================================

###### Custom ops end (tmp) ######


@attrs.define(frozen=True)
class DecimalOperation(UnaryOperation):
    """Operation that converts a value to Decimal."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Convert operand to Decimal."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        return Decimal(operand_val) if operand_val is not None else None


@attrs.define(frozen=True)
class ArrayIndexOperation(BinaryOperation):
    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get array element at specified index."""
        index_val, arr_val = self._resolve_operands(tree, ctx, vars)
        try:
            if not isinstance(arr_val, list):
                raise TypeError(f"Expected list for array indexing, got {type(arr_val).__name__}")
            if not isinstance(index_val, int):
                raise TypeError(f"Expected int for array index, got {type(index_val).__name__}")
            return arr_val[index_val]
        except IndexError as e:
            raise ValueError(
                f"Index {index_val} out of range for array of length {len(arr_val)}"
            ) from e


@attrs.define(frozen=True)
class IndexOperation(BinaryOperation):
    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get element at specified index."""
        idx = self.s__resolve_operand(self.right, tree, ctx, vars)

        with tree.at(*self.left.operand.components).with_list_view() as lv:
            return lv.get(idx)


@attrs.define(frozen=True)
class ArraySliceOperation(BinaryOperation):
    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get array slice from start to end indices."""
        start = self.s__resolve_operand(self.right[0], tree, ctx, vars)
        end = self.s__resolve_operand(self.right[1], tree, ctx, vars)

        with tree.at(*self.left.operand.components).with_list_view() as lv:
            if end is None:
                end = lv.length() - 1
            items = []
            for i in range(start, end + 1):
                items.append(lv.get(i))
        return items


@attrs.define(frozen=True)
class DictValueOperation(BinaryOperation):
    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get dictionary value for specified key."""
        dict_val, key_val = self._resolve_operands(tree, ctx, vars)
        try:
            if not isinstance(dict_val, dict):
                raise TypeError(f"Expected dict for key lookup, got {type(dict_val).__name__}")
            return dict_val[key_val]
        except KeyError as e:
            raise ValueError(f"Key {key_val} not found in dictionary") from e
        except TypeError as e:
            raise ValueError(f"Cannot lookup key with {type(key_val).__name__}") from e


@attrs.define(frozen=True)
class ListLengthOperation(UnaryOperation):
    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get length of list."""
        with tree.at(*self.operand.operand.components).with_list_view() as lv:
            return lv.length()


###### Custom ops end (tmp) ######


@attrs.define(frozen=True)
class AddOperation(BinaryOperation):
    """Addition operation: left + right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Perform addition of two operands."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.add(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot add {type(left_val).__name__} and {type(right_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class SubtractOperation(BinaryOperation):
    """Subtraction operation: left - right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Perform subtraction of two operands."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.sub(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot subtract {type(right_val).__name__} from {type(left_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class MultiplyOperation(BinaryOperation):
    """Multiplication operation: left * right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Perform multiplication of two operands."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.mul(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot multiply {type(left_val).__name__} and {type(right_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class DivideOperation(BinaryOperation):
    """Division operation: left / right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Perform division of two operands."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            if right_val == 0:
                raise ZeroDivisionError("Division by zero")
            return operator.truediv(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot divide {type(left_val).__name__} by {type(right_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class ModuloOperation(BinaryOperation):
    """Modulo operation: left % right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Perform modulo of two operands."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            if right_val == 0:
                raise ZeroDivisionError("Modulo by zero")
            return operator.mod(left_val, right_val)
        except TypeError as e:
            raise ValueError(
                f"Cannot perform modulo on {type(left_val).__name__} and {type(right_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class PowerOperation(BinaryOperation):
    """Power operation: left ** right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Perform power operation of two operands."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.pow(left_val, right_val)
        except (TypeError, OverflowError) as e:
            raise ValueError(
                f"Cannot raise {type(left_val).__name__} to power of {type(right_val).__name__}"
            ) from e


@attrs.define(frozen=True)
class AbsOperation(UnaryOperation):
    """Absolute value operation: abs(operand)."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get absolute value of operand."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            return abs(operand_val)
        except TypeError as e:
            raise ValueError(f"Cannot get absolute value of {type(operand_val).__name__}") from e


# =============================================================================
# COMPARISON OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class GreaterThanOperation(BinaryOperation):
    """Greater than operation: left > right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform greater than comparison."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.gt(left_val, right_val)
        except TypeError:
            # Handle incomparable types gracefully
            return False


@attrs.define(frozen=True)
class LessThanOperation(BinaryOperation):
    """Less than operation: left < right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform less than comparison."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.lt(left_val, right_val)
        except TypeError:
            return False


@attrs.define(frozen=True)
class GreaterEqualOperation(BinaryOperation):
    """Greater than or equal operation: left >= right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform greater than or equal comparison."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.ge(left_val, right_val)
        except TypeError:
            return False


@attrs.define(frozen=True)
class LessEqualOperation(BinaryOperation):
    """Less than or equal operation: left <= right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform less than or equal comparison."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return operator.le(left_val, right_val)
        except TypeError:
            return False


@attrs.define(frozen=True)
class EqualOperation(BinaryOperation):
    """Equality operation: left == right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform equality comparison."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        return left_val == right_val


@attrs.define(frozen=True)
class NotEqualOperation(BinaryOperation):
    """Not equal operation: left != right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform not equal comparison."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        return left_val != right_val


# =============================================================================
# LOGICAL OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class AndOperation(BinaryOperation):
    """Logical AND operation: left and right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform logical AND with short-circuit evaluation."""
        left_val = self.s__resolve_operand(self.left, tree, ctx, vars)
        if not left_val:
            return False  # Short-circuit
        right_val = self.s__resolve_operand(self.right, tree, ctx, vars)
        return bool(left_val) and bool(right_val)


@attrs.define(frozen=True)
class OrOperation(BinaryOperation):
    """Logical OR operation: left or right."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform logical OR with short-circuit evaluation."""
        left_val = self.s__resolve_operand(self.left, tree, ctx, vars)
        if left_val:
            return True  # Short-circuit
        right_val = self.s__resolve_operand(self.right, tree, ctx, vars)
        return bool(left_val) or bool(right_val)


@attrs.define(frozen=True)
class NotOperation(UnaryOperation):
    """Logical NOT operation: not operand."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Perform logical NOT."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        return not bool(operand_val)


# =============================================================================
# STRING OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class ContainsOperation(BinaryOperation):
    """Contains operation: right in left."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Check if right operand is contained in left operand."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return right_val in left_val
        except TypeError:
            return False


@attrs.define(frozen=True)
class StartsWithOperation(BinaryOperation):
    """String starts with operation: left.startswith(right)."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Check if left operand starts with right operand."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return str(left_val).startswith(str(right_val))
        except (TypeError, AttributeError):
            return False


@attrs.define(frozen=True)
class EndsWithOperation(BinaryOperation):
    """String ends with operation: left.endswith(right)."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Check if left operand ends with right operand."""
        left_val, right_val = self._resolve_operands(tree, ctx, vars)
        try:
            return str(left_val).endswith(str(right_val))
        except (TypeError, AttributeError):
            return False


# =============================================================================
# FUNCTION OPERATIONS
# =============================================================================


@attrs.define(frozen=True)
class LengthOperation(UnaryOperation):
    """Length operation: len(operand)."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> int:
        """Get length of operand."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            return len(operand_val)
        except TypeError as e:
            raise ValueError(f"Cannot get length of {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class MaxOperation(UnaryOperation):
    """Maximum operation: max(operand)."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get maximum value from operand."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            return max(operand_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot get max of {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class MinOperation(UnaryOperation):
    """Minimum operation: min(operand)."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get minimum value from operand."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            return min(operand_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot get min of {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class SumOperation(UnaryOperation):
    """Sum operation: sum(operand)."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> Any:
        """Get sum of operand values."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            return sum(operand_val)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot get sum of {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class AnyOperation(UnaryOperation):
    """Any operation: any(operand) - returns True if any element is truthy."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Check if any element in operand is truthy."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            return any(operand_val)
        except TypeError as e:
            raise ValueError(f"Cannot check any() on {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class EveryOperation(UnaryOperation):
    """Every operation: all(operand) - returns True if all elements are truthy."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Check if all elements in operand are truthy."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            return all(operand_val)
        except TypeError as e:
            raise ValueError(f"Cannot check all() on {type(operand_val).__name__}") from e


@attrs.define(frozen=True)
class BoolOperation(UnaryOperation):
    """Bool operation: bool(operand) - converts operand to boolean."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> bool:
        """Convert operand to boolean."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        return bool(operand_val)


@attrs.define(frozen=True)
class CountOperation(UnaryOperation):
    """Count operation: count non-None values in operand."""

    def calc(self, tree: Tree, ctx: Any, vars: dict[str | int, Any]) -> int:
        """Count non-None values in operand."""
        operand_val = self._resolve_operand(tree, ctx, vars)
        try:
            if hasattr(operand_val, "__iter__") and not isinstance(operand_val, (str, bytes)):
                return sum(1 for item in operand_val if item is not None)
            else:
                return 1 if operand_val is not None else 0
        except TypeError as e:
            raise ValueError(f"Cannot count values in {type(operand_val).__name__}") from e
