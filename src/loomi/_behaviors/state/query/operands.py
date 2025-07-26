"""
Operand implementations for the query system.

This module provides different types of operands that can be used
in query operations, including path operands, literal values,
and nested queries.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .exceptions import OperandResolutionError, PathNotFoundError
from .types import EvaluatorProtocol, Path, QueryProtocol

if TYPE_CHECKING:
    from ..tree import Tree

__all__ = [
    "PathOperand",
    "LiteralOperand",
    "QueryOperand",
    "FunctionOperand",
]


class Operand(ABC):
    """
    Base class for all operand implementations.

    Operands represent values that can be resolved in the context
    of a tree and evaluation environment.
    """

    @abstractmethod
    def resolve(
        self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol | None = None
    ) -> Any:
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


class PathOperand(Operand):
    """
    Operand representing a path in the tree.

    This operand navigates through the tree structure to resolve
    to the value at the specified path.
    """

    def __init__(self, path: Path):
        """
        Initialize path operand.

        Args:
            path: List of path components to navigate
        """
        self.path = path.copy()

    def resolve(
        self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol | None = None
    ) -> Any:
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
            if not self.path:
                raise PathNotFoundError(self.path)

            # Phase 1: Navigate tree with leading string components
            i = 0
            while i < len(self.path) - 1 and isinstance(self.path[i], str):
                i += 1

            current_tree = tree.at(*self.path[:i], ctx=ctx) if i > 0 else tree  # type: ignore
            current_view = None

            # Phase 2: Navigate through views for remaining components
            while i < len(self.path) - 1:
                component = self.path[i]
                next_component = self.path[i + 1]

                if current_view is None:
                    current_view = self._create_view_for_next(current_tree, next_component, ctx)

                current_view = self._navigate_view(current_view, component, next_component)
                i += 1

            # Phase 3: Extract final value
            last_component = self.path[-1]
            if current_view is None:
                current_view = self._create_view_for_component(current_tree, last_component, ctx)

            return current_view.get(last_component)  # type: ignore

        except Exception as e:
            if isinstance(e, PathNotFoundError):
                raise
            raise OperandResolutionError(
                "path",
                f"Failed to resolve path {'.'.join(str(c) for c in self.path)}",
                original_error=e,
            ) from e

    def _create_view_for_next(self, tree: Tree, next_component: str | int, ctx: Any):
        """Create view based on what the next component needs."""
        if isinstance(next_component, str):
            return tree.dict_view(ctx=ctx)
        elif isinstance(next_component, int):
            return tree.list_view(ctx=ctx)

    def _create_view_for_component(self, tree: Tree, component: str | int, ctx: Any):
        """Create view based on the component type."""
        if isinstance(component, str):
            return tree.dict_view(ctx=ctx)
        elif isinstance(component, int):
            return tree.list_view(ctx=ctx)

    def _navigate_view(self, view, component: str | int, next_component: str | int):
        """Navigate view to next container based on next component type."""
        if isinstance(next_component, str):
            return view.dict_view(component)
        elif isinstance(next_component, int):
            return view.list_view(component)

    def __repr__(self) -> str:
        path_str = ".".join([str(p) for p in self.path]) if self.path else "root"
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

    def resolve(
        self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol | None = None
    ) -> Any:
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

    def resolve(
        self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol | None = None
    ) -> Any:
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

    def resolve(
        self, tree: Tree, ctx: Any = None, evaluator: EvaluatorProtocol | None = None
    ) -> Any:
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
