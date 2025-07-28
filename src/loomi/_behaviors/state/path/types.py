"""
Type definitions for the path module.

This module defines the core types and protocols used in path operations,
providing clear interfaces and type safety for path construction and evaluation.
"""

from __future__ import annotations

from typing import Any, Protocol

__all__ = [
    "PathComponent",
    "PathResult",
    "PathProtocol",
    "PathEvaluatorProtocol",
]

# Basic path types
PathComponent = str | int
"""A single component of a path - either a string key or integer index."""

PathResult = Any
"""Result of evaluating a path - can be any value from the tree."""


class PathProtocol(Protocol):
    """Protocol for path-like objects."""

    @property
    def components(self) -> tuple[PathComponent, ...]:
        """Get path components as immutable tuple."""
        ...

    @property
    def tree(self) -> Any:  # Tree type - avoiding circular import
        """Get reference to tree instance."""
        ...

    def evaluate(self, ctx: Any = None) -> PathResult:
        """Evaluate path against tree data."""
        ...

    def exists(self, ctx: Any = None) -> bool:
        """Check if path exists in tree."""
        ...

    def parent(self) -> PathProtocol | None:
        """Get parent path."""
        ...

    def join(self, *components: PathComponent) -> PathProtocol:
        """Join additional components."""
        ...


class PathEvaluatorProtocol(Protocol):
    """Protocol for path evaluator implementations."""

    def evaluate(self, path: PathProtocol, ctx: Any = None) -> PathResult:
        """
        Evaluate a path against tree data.

        Args:
            path: Path to evaluate
            ctx: Optional context

        Returns:
            Value at path location
        """
        ...
