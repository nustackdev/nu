"""
Base class for all expression nodes.

This module provides the Expression class, which all expressions
should inherit from to ensure consistent behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .metadata import ExpressionMetadata
from .node import DAGNodeMixin
from .types import ErrorBehavior

if TYPE_CHECKING:
    from loomi.evaluator.context import Context
    from loomi.evaluator.runtime import Runtime


class Expression(ABC, DAGNodeMixin["Expression"]):
    """
    Base class for all expressions.

    Implements common functionality for expressions, including error handling,
    logging, and tracing. All expressions should inherit from this class.

    Args:
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs
    """

    def __init__(
        self,
        *,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Expression | None = None,
    ):
        """
        Initialize the expression.

        Args:
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs
        """
        super().__init__()

        if error_behavior not in ("fail", "continue"):
            raise ValueError(f"Invalid error_behavior: {error_behavior}")

        self._error_behavior = error_behavior
        self._on_fail = on_fail

    @property
    def metadata(self) -> ExpressionMetadata:
        """
        Get the expression's metadata.

        The metadata includes the expression's name, description, and any
        custom properties. By default, the name is the class name and
        the description is the class docstring.

        Returns:
            The expression metadata
        """
        return ExpressionMetadata(
            name=self.__class__.__name__,
            description=self.__doc__ or "",
            custom_properties={},
        )

    def __repr__(self):
        """Return a string representation of the expression."""
        return (
            f"{self.__class__.__name__}("
            f"error_behavior={self._error_behavior}, "
            f"on_fail={self._on_fail})"
        )

    @abstractmethod
    def evaluate(self, runtime: "Runtime", context: "Context") -> None:
        """
        Evaluate the expression.

        This method should be implemented by subclasses to perform the
        actual evaluation logic.

        Args:
            runtime: The runtime environment in which the expression is evaluated
            context: The execution context
        """
        pass
