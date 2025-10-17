"""Base term (AST node) definitions.

Provides the fundamental Term hierarchy:
- Term: Base class for all AST nodes
- PathTerm: L-values (assignable locations)
- ValueTerm: R-values (computed values)
- CommandTerm: Impure operations with side effects
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from redwood.dsl.metadata import TermMetadata


if TYPE_CHECKING:
    from redwood.tree.context import ContextType
    from redwood.tree.tree import Tree


class Term(ABC):
    """Base class for all DSL terms (AST nodes).

    Terms represent lazy computations that are only executed when
    .evaluate() is called. They carry metadata for static analysis
    and optimization.

    The term hierarchy:
    - PathTerm: Locations that can be read/written (L-values)
    - ValueTerm: Pure computed values (R-values)
    - CommandTerm: Impure operations with side effects

    Attributes:
        meta: Metadata computed during construction
    """

    def __init__(self) -> None:
        """Initialize term with default metadata."""
        self.meta = TermMetadata()

    @abstractmethod
    def evaluate(self, tree: "Tree", ctx: "ContextType") -> Any:
        """Evaluate term against tree with context.

        Args:
            tree: Tree instance for navigation and view access
            ctx: Context (transaction or snapshot) for data access

        Returns:
            Evaluation result: actual value, Empty, or NaN

        Raises:
            DSLError: On DSL-specific evaluation errors
        """
        pass


class PathTerm(Term):
    """L-value: assignable location in tree.

    PathTerms represent navigable locations in the tree. They can be:
    - Read via parent view's .get() method
    - Written via parent view's .set() method (if supported)
    - Deleted via parent view's .delete() method (if supported)

    Path operations respect view protocols - all access goes through
    the parent view, not directly to storage.
    """

    def __init__(self) -> None:
        """Initialize path term with pure metadata."""
        super().__init__()
        self.meta.is_pure = True

    @abstractmethod
    def resolve_path(self, tree: "Tree", ctx: "ContextType") -> tuple[str, ...]:
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
            >>> # Dynamic path
            >>> path.resolve_path(tree, ctx)  # Evaluates indices first
        """
        pass

    @abstractmethod
    def parent_path(self) -> "PathTerm | None":
        """Get parent path.

        Returns:
            Parent PathTerm, or None if this is root

        Examples:
            >>> path = Market.orders["AAPL"].price
            >>> parent = path.parent_path()  # Market.orders["AAPL"]
        """
        pass

    @abstractmethod
    def last_segment(self) -> str:
        """Get last path segment.

        Returns:
            Last segment as string

        Examples:
            >>> Market.orders["AAPL"].price.last_segment()  # "price"
            >>> Market.orders["AAPL"].last_segment()  # "AAPL"
        """
        pass

    # ========================================================================
    # Operator overloading - implicit .get() in value contexts
    # ========================================================================

    def _wrap_value(self, other: Any) -> "ValueTerm":
        """Wrap value as ValueTerm if needed (helper)."""
        from redwood.dsl.values import LiteralValue

        if isinstance(other, ValueTerm):
            return other
        return LiteralValue(other)

    def _to_value(self) -> "ValueTerm":
        """Convert path to value term (helper)."""
        from redwood.dsl.values import PathValue

        return PathValue(self)

    # Comparison operators
    def __gt__(self, other: Any) -> "ValueTerm":
        """Greater than: path > value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("gt", self._to_value(), self._wrap_value(other))

    def __lt__(self, other: Any) -> "ValueTerm":
        """Less than: path < value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("lt", self._to_value(), self._wrap_value(other))

    def __eq__(self, other: Any) -> "ValueTerm":  # type: ignore[override]
        """Equality: path == value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("eq", self._to_value(), self._wrap_value(other))

    def __ne__(self, other: Any) -> "ValueTerm":  # type: ignore[override]
        """Inequality: path != value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("ne", self._to_value(), self._wrap_value(other))

    def __ge__(self, other: Any) -> "ValueTerm":
        """Greater or equal: path >= value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("ge", self._to_value(), self._wrap_value(other))

    def __le__(self, other: Any) -> "ValueTerm":
        """Less or equal: path <= value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("le", self._to_value(), self._wrap_value(other))

    # Arithmetic operators
    def __add__(self, other: Any) -> "ValueTerm":
        """Addition: path + value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("add", self._to_value(), self._wrap_value(other))

    def __sub__(self, other: Any) -> "ValueTerm":
        """Subtraction: path - value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("sub", self._to_value(), self._wrap_value(other))

    def __mul__(self, other: Any) -> "ValueTerm":
        """Multiplication: path * value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("mul", self._to_value(), self._wrap_value(other))

    def __truediv__(self, other: Any) -> "ValueTerm":
        """Division: path / value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("div", self._to_value(), self._wrap_value(other))

    # Logical operators
    def __and__(self, other: Any) -> "ValueTerm":
        """Logical AND: path & value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("and", self._to_value(), self._wrap_value(other))

    def __or__(self, other: Any) -> "ValueTerm":
        """Logical OR: path | value (implicit .get())."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("or", self._to_value(), self._wrap_value(other))

    # Commands
    def delete(self) -> "CommandTerm":
        """Create delete command.

        Returns:
            DeleteCommand that removes this path

        Example:
            User.age.delete().evaluate(tree, ctx)
        """
        from redwood.dsl.commands import DeleteCommand

        return DeleteCommand(self)

    def update(self, fn: Callable[[Any], Any]) -> "CommandTerm":
        """Create update command.

        Args:
            fn: Transformation function (current_value) -> new_value

        Returns:
            UpdateCommand that updates this path

        Example:
            User.age.update(lambda x: x + 1).evaluate(tree, ctx)
        """
        from redwood.dsl.commands import UpdateCommand

        return UpdateCommand(self, fn)


class ValueTerm(Term):
    """R-value: computed value (pure).

    ValueTerms represent pure computations with no side effects.
    They can be composed using operators to build complex expressions.

    Cannot be assigned to - only evaluated to produce a result.
    """

    def __init__(self) -> None:
        """Initialize value term with pure metadata."""
        super().__init__()
        self.meta.is_pure = True

    # ========================================================================
    # Operator overloading for ValueTerm composition
    # ========================================================================

    def _wrap_value(self, other: Any) -> "ValueTerm":
        """Wrap value as ValueTerm if needed (helper)."""
        from redwood.dsl.values import LiteralValue

        if isinstance(other, ValueTerm):
            return other
        return LiteralValue(other)

    # Comparison operators
    def __gt__(self, other: Any) -> "ValueTerm":
        """Greater than: value > other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("gt", self, self._wrap_value(other))

    def __lt__(self, other: Any) -> "ValueTerm":
        """Less than: value < other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("lt", self, self._wrap_value(other))

    def __eq__(self, other: Any) -> "ValueTerm":  # type: ignore[override]
        """Equality: value == other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("eq", self, self._wrap_value(other))

    def __ne__(self, other: Any) -> "ValueTerm":  # type: ignore[override]
        """Inequality: value != other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("ne", self, self._wrap_value(other))

    def __ge__(self, other: Any) -> "ValueTerm":
        """Greater or equal: value >= other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("ge", self, self._wrap_value(other))

    def __le__(self, other: Any) -> "ValueTerm":
        """Less or equal: value <= other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("le", self, self._wrap_value(other))

    # Arithmetic operators
    def __add__(self, other: Any) -> "ValueTerm":
        """Addition: value + other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("add", self, self._wrap_value(other))

    def __sub__(self, other: Any) -> "ValueTerm":
        """Subtraction: value - other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("sub", self, self._wrap_value(other))

    def __mul__(self, other: Any) -> "ValueTerm":
        """Multiplication: value * other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("mul", self, self._wrap_value(other))

    def __truediv__(self, other: Any) -> "ValueTerm":
        """Division: value / other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("div", self, self._wrap_value(other))

    # Logical operators
    def __and__(self, other: Any) -> "ValueTerm":
        """Logical AND: value & other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("and", self, self._wrap_value(other))

    def __or__(self, other: Any) -> "ValueTerm":
        """Logical OR: value | other."""
        from redwood.dsl.values import BinaryOp

        return BinaryOp("or", self, self._wrap_value(other))

    def __invert__(self) -> "ValueTerm":
        """Logical NOT: ~value."""
        from redwood.dsl.values import UnaryOp

        return UnaryOp("not", self)


class CommandTerm(Term):
    """Impure operation with side effects.

    CommandTerms modify tree state and always have is_pure=False
    in metadata. They represent mutations like set, delete, or
    update operations.

    Examples:
        - Market.price.set(100.0)
        - Market.orders["AAPL"].delete()
        - Market.counter.update(lambda x: x + 1)
    """

    def __init__(self) -> None:
        """Initialize command term with impure metadata."""
        super().__init__()
        self.meta.is_pure = False
        self.meta.has_side_effects = True
