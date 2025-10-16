"""Base term (AST node) definitions.

This module provides the fundamental Term hierarchy:
- Term: Base class for all AST nodes
- PathTerm: L-values (assignable locations)
- ValueTerm: R-values (computed values)
- CommandTerm: Impure operations with side effects
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from redwood.dsl.metadata import TermMetadata
from redwood.dsl.types import TermResult


if TYPE_CHECKING:
    from redwood.tree import ContextType, Tree

__all__ = ["CommandTerm", "PathTerm", "Term", "ValueTerm"]


class Term(ABC):
    """Base class for all DSL terms (AST nodes).

    All terms are immutable and frozen after construction. They represent
    lazy computations that are only executed when .evaluate() is called.

    The term hierarchy:
    - PathTerm: Locations that can be read/written (L-values)
    - ValueTerm: Pure computed values (R-values)
    - CommandTerm: Impure operations with side effects

    Attributes:
        meta: Immutable metadata computed during construction
    """

    def __init__(self) -> None:
        """Initialize with default metadata.

        Subclasses should override and set appropriate metadata fields.
        """
        self.meta = TermMetadata()

    @abstractmethod
    def evaluate(self, tree: Tree, ctx: ContextType) -> TermResult[Any]:
        """Evaluate term against tree with context.

        Args:
            tree: Tree instance for navigation and view access
            ctx: Context (transaction or snapshot) for data access

        Returns:
            Evaluation result: actual value, SpecialValue.EMPTY, or SpecialValue.NAN

        Raises:
            DSLError: On DSL-specific evaluation errors
            Native Python errors: On type mismatches, etc.
        """


class PathTerm(Term):
    """L-value: assignable location in tree.

    PathTerms represent navigable locations in the tree. They can be:
    - Read via parent view's .get() method
    - Written via parent view's .set() method (if supported)
    - Deleted via parent view's .delete() method (if supported)

    Path operations respect view protocols - all access goes through the parent
    view, not directly to storage.
    """

    def get(self) -> ValueTerm:
        """Convert path to value term (explicit read operation).

        Returns:
            ValueTerm that reads this path when evaluated

        Examples:
            >>> price = Market.orders["AAPL"].price.get()
            >>> value = price.evaluate(tree, ctx)  # Reads via parent view
        """
        from redwood.dsl.values import PathValue

        return PathValue(self)

    def set(self, value: Any) -> CommandTerm:
        """Create set command for this path.

        Args:
            value: Value to set (can be another term or Python value)

        Returns:
            CommandTerm that sets this path when evaluated

        Examples:
            >>> cmd = Market.orders["AAPL"].price.set(155.0)
            >>> cmd.evaluate(tree, ctx)  # Executes via parent view
        """
        from redwood.dsl.commands import SetCommand

        return SetCommand(self, value)

    def delete(self) -> CommandTerm:
        """Create delete command for this path.

        Returns:
            CommandTerm that deletes this path when evaluated

        Examples:
            >>> cmd = Market.orders["AAPL"].delete()
            >>> cmd.evaluate(tree, ctx)  # Executes via parent view
        """
        from redwood.dsl.commands import DeleteCommand

        return DeleteCommand(self)

    @abstractmethod
    def resolve_path(self, tree: Tree, ctx: ContextType) -> tuple[str, ...]:
        """Resolve path to tuple of segments.

        For static paths, returns immediately without tree access.
        For dynamic paths (with runtime indices), evaluates indices.

        Args:
            tree: Tree instance for dynamic index resolution
            ctx: Context for dynamic index evaluation

        Returns:
            Tuple of path segments

        Examples:
            >>> # Static path
            >>> path.resolve_path(tree, ctx)  # ("orders", "AAPL", "price")
            >>>
            >>> # Dynamic path
            >>> path.resolve_path(tree, ctx)  # Evaluates User.current_symbol first
        """

    @abstractmethod
    def parent_path(self) -> PathTerm | None:
        """Get parent path.

        Returns:
            Parent PathTerm, or None if this is root

        Examples:
            >>> path = Market.orders["AAPL"].price
            >>> parent = path.parent_path()  # Market.orders["AAPL"]
        """

    @abstractmethod
    def last_segment(self) -> str | ValueTerm:
        """Get last path segment.

        Returns:
            Last segment as string (for FieldPath) or ValueTerm (for IndexPath)

        Examples:
            >>> Market.orders["AAPL"].price.last_segment()  # "price"
            >>> Market.orders["AAPL"].last_segment()  # "AAPL" (as LiteralValue)
        """


class ValueTerm(Term):
    """R-value: computed value (pure).

    ValueTerms represent pure computations with no side effects. They can be
    composed using operators to build complex expressions.

    Cannot be assigned to - only evaluated to produce a result.
    """

    def __gt__(self, other: Any) -> ValueTerm:
        """Greater than comparison.

        Args:
            other: Value or term to compare against

        Returns:
            BoolValue term representing comparison
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("gt", self, _wrap_value(other))

    def __lt__(self, other: Any) -> ValueTerm:
        """Less than comparison.

        Args:
            other: Value or term to compare against

        Returns:
            BoolValue term representing comparison
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("lt", self, _wrap_value(other))

    def __eq__(self, other: Any) -> ValueTerm:  # type: ignore[override]
        """Equality comparison.

        Args:
            other: Value or term to compare against

        Returns:
            BoolValue term representing comparison
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("eq", self, _wrap_value(other))

    def __ne__(self, other: Any) -> ValueTerm:  # type: ignore[override]
        """Inequality comparison.

        Args:
            other: Value or term to compare against

        Returns:
            BoolValue term representing comparison
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("ne", self, _wrap_value(other))

    def __add__(self, other: Any) -> ValueTerm:
        """Addition operation.

        Args:
            other: Value or term to add

        Returns:
            ValueTerm representing addition
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("add", self, _wrap_value(other))

    def __sub__(self, other: Any) -> ValueTerm:
        """Subtraction operation.

        Args:
            other: Value or term to subtract

        Returns:
            ValueTerm representing subtraction
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("sub", self, _wrap_value(other))

    def __mul__(self, other: Any) -> ValueTerm:
        """Multiplication operation.

        Args:
            other: Value or term to multiply by

        Returns:
            ValueTerm representing multiplication
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("mul", self, _wrap_value(other))

    def __truediv__(self, other: Any) -> ValueTerm:
        """Division operation.

        Args:
            other: Value or term to divide by

        Returns:
            ValueTerm representing division
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("div", self, _wrap_value(other))

    def __and__(self, other: Any) -> ValueTerm:
        """Logical AND operation.

        Args:
            other: Value or term to AND with

        Returns:
            ValueTerm representing logical AND
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("and", self, _wrap_value(other))

    def __or__(self, other: Any) -> ValueTerm:
        """Logical OR operation.

        Args:
            other: Value or term to OR with

        Returns:
            ValueTerm representing logical OR
        """
        from redwood.dsl.values import BinaryOp

        return BinaryOp("or", self, _wrap_value(other))

    def __invert__(self) -> ValueTerm:
        """Logical NOT operation.

        Returns:
            ValueTerm representing logical NOT
        """
        from redwood.dsl.values import UnaryOp

        return UnaryOp("not", self)


class CommandTerm(Term):
    """Impure operation with side effects.

    CommandTerms modify tree state and always have is_pure=False in metadata.
    They represent mutations like set, delete, or update operations.

    Examples:
        - Market.price.set(100.0)
        - Market.orders["AAPL"].delete()
        - Market.counter.update(lambda x: x + 1)
    """

    def __init__(self) -> None:
        """Initialize with impure metadata."""
        super().__init__()
        self.meta = self.meta.mark_impure()


def _wrap_value(value: Any) -> ValueTerm:
    """Wrap Python value as LiteralValue term if needed.

    Args:
        value: Value to wrap (can be ValueTerm or Python value)

    Returns:
        ValueTerm (original if already a term, wrapped otherwise)
    """
    from redwood.dsl.values import LiteralValue

    if isinstance(value, ValueTerm):
        return value
    return LiteralValue(value)
