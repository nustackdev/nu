"""
Core interfaces and base classes for the query system.

This module provides the fundamental abstractions that all query
components build upon, including Query, Operation, and Operand base classes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .exceptions import QueryEvaluationError
from .types import EvaluatorProtocol, OperandProtocol, OperationProtocol, QueryResult

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "Query",
    "Operation",
    "Operand",
    "LazyOperation",
    "ValueQuery",
]


class Query(ABC):
    """
    Base class for all query implementations.

    Queries are immutable objects that represent a complete query
    that can be evaluated against tree data to produce a result.
    """

    @abstractmethod
    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate this query against the provided tree.

        Args:
            tree: Tree instance to query against
            ctx: Optional context (transaction/snapshot)

        Returns:
            Query evaluation result

        Raises:
            QueryEvaluationError: If evaluation fails
        """
        pass

    def __eq__(self, other: object) -> bool:
        """Default equality based on class and attributes."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Default hash based on class and hashable attributes."""
        hashable_attrs = tuple(
            v
            for v in self.__dict__.values()
            if isinstance(v, (str, int, float, bool, tuple, type(None)))
        )
        return hash((self.__class__, hashable_attrs))


class Operation(ABC):
    """
    Base class for all operation implementations.

    Operations define how to combine operands to produce results.
    They are stateless and can be reused across multiple queries.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this operation."""
        pass

    @property
    def is_unary(self) -> bool:
        """Whether this operation takes a single operand."""
        return False

    @abstractmethod
    def execute(self, left: Any, right: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        """
        Execute operation with the given operand values.

        Args:
            left: Left operand value
            right: Right operand value (None for unary operations)
            evaluator: Evaluator instance for nested operations

        Returns:
            Operation result

        Raises:
            OperationNotSupportedError: If operation not supported on operand types
        """
        pass

    def __eq__(self, other: object) -> bool:
        """Operations are equal if they have the same class."""
        return isinstance(other, self.__class__)

    def __hash__(self) -> int:
        """Hash based on operation class."""
        return hash(self.__class__)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class Operand(ABC):
    """
    Base class for all operand implementations.

    Operands represent values that can be resolved in the context
    of a tree and evaluation environment.
    """

    @abstractmethod
    def resolve(self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        """
        Resolve this operand to its actual value.

        Args:
            tree: Tree instance to resolve against
            ctx: Optional context (transaction/snapshot)
            evaluator: Evaluator instance for nested resolution

        Returns:
            Resolved value

        Raises:
            OperandResolutionError: If operand cannot be resolved
        """
        pass

    def __eq__(self, other: object) -> bool:
        """Default equality based on class and attributes."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Default hash based on class and hashable attributes."""
        hashable_attrs = tuple(
            v
            for v in self.__dict__.values()
            if isinstance(v, (str, int, float, bool, tuple, type(None)))
        )
        return hash((self.__class__, hashable_attrs))


class LazyOperation(Query):
    """
    A query that represents a lazy operation between operands.

    This captures an operation (like >, <, ==) and its operands
    without immediately executing it. Evaluation happens later
    when .evaluate() is called.
    """

    def __init__(
        self, left: OperandProtocol, operation: OperationProtocol, right: OperandProtocol = None
    ):
        """
        Initialize lazy operation.

        Args:
            left: Left operand
            operation: Operation to apply
            right: Right operand (None for unary operations)
        """
        self.left = left
        self.operation = operation
        self.right = right

        # Validate operation arity
        if operation.is_unary and right is not None:
            raise ValueError(f"Unary operation {operation.name} cannot have right operand")
        if not operation.is_unary and right is None:
            raise ValueError(f"Binary operation {operation.name} requires right operand")

    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate the lazy operation.

        Args:
            tree: Tree instance
            ctx: Optional context

        Returns:
            Operation result
        """
        from .evaluator import QueryEvaluator  # Avoid circular import

        evaluator = QueryEvaluator()

        try:
            # Resolve operands
            left_value = evaluator.resolve_operand(self.left, tree, ctx)
            right_value = evaluator.resolve_operand(self.right, tree, ctx) if self.right else None

            # Execute operation
            return evaluator.execute_operation(self.operation, left_value, right_value)

        except Exception as e:
            raise QueryEvaluationError(
                f"Failed to evaluate lazy operation: {self.operation.name}", original_error=e
            ) from e

    # =========================================================================
    # LOGICAL OPERATIONS FOR CHAINING LAZY OPERATIONS
    # =========================================================================

    def __and__(self, other: LazyOperation) -> LazyOperation:
        """
        Logical AND: operation1 & operation2

        Args:
            other: Other LazyOperation to combine with

        Returns:
            New LazyOperation representing the AND operation
        """
        from .operands import QueryOperand  # Avoid circular import
        from .operations import OPERATIONS

        return LazyOperation(
            left=QueryOperand(self), operation=OPERATIONS["and"], right=QueryOperand(other)
        )

    def __or__(self, other: LazyOperation) -> LazyOperation:
        """
        Logical OR: operation1 | operation2

        Args:
            other: Other LazyOperation to combine with

        Returns:
            New LazyOperation representing the OR operation
        """
        from .operands import QueryOperand  # Avoid circular import
        from .operations import OPERATIONS

        return LazyOperation(
            left=QueryOperand(self), operation=OPERATIONS["or"], right=QueryOperand(other)
        )

    def __invert__(self) -> LazyOperation:
        """
        Logical NOT: ~operation

        Returns:
            New LazyOperation representing the NOT operation
        """
        from .operands import QueryOperand  # Avoid circular import
        from .operations import OPERATIONS

        return LazyOperation(left=QueryOperand(self), operation=OPERATIONS["not"])

    def __repr__(self) -> str:
        if self.operation.is_unary:
            return f"LazyOperation({self.operation.name} {self.left})"
        return f"LazyOperation({self.left} {self.operation.name} {self.right})"


class ValueQuery(Query):
    """
    A query that extracts a value from a single operand.

    This is used for terminal operations that just return
    the resolved value of an operand.
    """

    def __init__(self, operand: OperandProtocol):
        """
        Initialize value query.

        Args:
            operand: Operand to extract value from
        """
        self.operand = operand

    def evaluate(self, tree: Tree, ctx: Any = None) -> QueryResult:
        """
        Evaluate by resolving the operand.

        Args:
            tree: Tree instance
            ctx: Optional context

        Returns:
            Operand value
        """
        from .evaluator import QueryEvaluator  # Avoid circular import

        evaluator = QueryEvaluator()

        try:
            return evaluator.resolve_operand(self.operand, tree, ctx)
        except Exception as e:
            raise QueryEvaluationError("Failed to evaluate value query", original_error=e) from e

    def __repr__(self) -> str:
        return f"ValueQuery({self.operand})"
