"""
Operand implementations for the query system.

This module provides different types of operands that can be used
in query operations, including path operands, literal values,
and nested queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..tree.types import EMPTY
from .core import Operand
from .exceptions import OperandResolutionError, PathNotFoundError
from .types import EvaluatorProtocol, PathList, QueryProtocol

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "PathOperand",
    "LiteralOperand",
    "QueryOperand",
    "FunctionOperand",
]


class PathOperand(Operand):
    """
    Operand representing a path in the tree.

    This operand navigates through the tree structure to resolve
    to the value at the specified path.
    """

    def __init__(self, path: PathList):
        """
        Initialize path operand.

        Args:
            path: List of path components to navigate
        """
        self.path = path.copy()  # Defensive copy

    def resolve(self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        """
        Resolve path to its value in the tree.

        Args:
            tree: Tree instance to navigate
            ctx: Optional context (transaction/snapshot)
            evaluator: Evaluator instance (unused for path operands)

        Returns:
            Value at the path

        Raises:
            PathNotFoundError: If path doesn't exist
            OperandResolutionError: If resolution fails
        """
        try:
            current_tree = tree

            # Navigate through path components
            for component in self.path:
                current_tree = current_tree.at(component)

            # Extract value based on tree type
            if current_tree.is_primitive():
                value = current_tree.get_primitive()
                if value is EMPTY:
                    raise PathNotFoundError(self.path)
                return value

            elif current_tree.is_mapping():
                dict_view = current_tree.dict_view(ctx=ctx)
                return dict(dict_view.items())

            elif current_tree.is_indexed():
                list_view = current_tree.list_view(ctx=ctx)
                return list(list_view.values())

            else:
                # Path exists but no data
                return None

        except Exception as e:
            if isinstance(e, PathNotFoundError):
                raise
            raise OperandResolutionError(
                "path", f"Failed to resolve path {'.'.join(self.path)}", original_error=e
            ) from e

    def __repr__(self) -> str:
        path_str = ".".join(self.path) if self.path else "root"
        return f"PathOperand({path_str})"


class LiteralOperand(Operand):
    """
    Operand representing a literal value.

    This operand simply returns its stored value without
    any resolution or tree navigation.
    """

    def __init__(self, value: Any):
        """
        Initialize literal operand.

        Args:
            value: Literal value to store
        """
        self.value = value

    def resolve(self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        """
        Resolve to the literal value.

        Args:
            tree: Tree instance (unused)
            ctx: Optional context (unused)
            evaluator: Evaluator instance (unused)

        Returns:
            The literal value
        """
        return self.value

    def __repr__(self) -> str:
        if isinstance(self.value, str):
            return f"LiteralOperand('{self.value}')"
        return f"LiteralOperand({self.value})"


class QueryOperand(Operand):
    """
    Operand that is itself a query.

    This allows nesting queries as operands in larger queries,
    enabling complex compositions.
    """

    def __init__(self, query: QueryProtocol):
        """
        Initialize query operand.

        Args:
            query: Query to use as operand
        """
        self.query = query

    def resolve(self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        """
        Resolve by evaluating the nested query.

        Args:
            tree: Tree instance
            ctx: Optional context
            evaluator: Evaluator instance

        Returns:
            Result of evaluating the nested query

        Raises:
            OperandResolutionError: If nested query evaluation fails
        """
        try:
            if evaluator:
                return evaluator.evaluate_query(self.query, tree, ctx)
            else:
                return self.query.evaluate(tree, ctx)
        except Exception as e:
            raise OperandResolutionError(
                "query", "Failed to resolve nested query operand", original_error=e
            ) from e

    def __repr__(self) -> str:
        return f"QueryOperand({self.query})"


class FunctionOperand(Operand):
    """
    Operand that applies a function to another operand.

    This enables function-like operations such as len(), max(), etc.
    that take an operand and transform it.
    """

    def __init__(self, function_name: str, operand: Operand, *args):
        """
        Initialize function operand.

        Args:
            function_name: Name of function to apply
            operand: Operand to apply function to
            *args: Additional arguments for the function
        """
        self.function_name = function_name
        self.operand = operand
        self.args = args

        # Registry of supported functions
        self._functions = {
            "len": len,
            "max": max,
            "min": min,
            "sum": sum,
            "abs": abs,
            "round": round,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "sorted": sorted,
            "reversed": lambda x: list(reversed(x)),
        }

    def resolve(self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol = None) -> Any:
        """
        Resolve by applying function to operand value.

        Args:
            tree: Tree instance
            ctx: Optional context
            evaluator: Evaluator instance

        Returns:
            Result of applying function

        Raises:
            OperandResolutionError: If function is unknown or execution fails
        """
        if self.function_name not in self._functions:
            raise OperandResolutionError("function", f"Unknown function: {self.function_name}")

        try:
            # Resolve the operand first
            if evaluator:
                value = evaluator.resolve_operand(self.operand, tree, ctx)
            else:
                value = self.operand.resolve(tree, ctx, evaluator)

            # Apply function
            function = self._functions[self.function_name]

            if self.args:
                return function(value, *self.args)
            else:
                return function(value)

        except Exception as e:
            raise OperandResolutionError(
                "function", f"Failed to apply function {self.function_name}", original_error=e
            ) from e

    def __repr__(self) -> str:
        if self.args:
            args_str = ", ".join(repr(arg) for arg in self.args)
            return f"FunctionOperand({self.function_name}({self.operand}, {args_str}))"
        return f"FunctionOperand({self.function_name}({self.operand}))"
