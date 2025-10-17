"""Base term (AST node) definitions.

Provides the fundamental Term hierarchy:
- Term: Base class for all AST nodes
- PathTerm: L-values (assignable locations)
- ValueTerm: R-values (computed values)
- CommandTerm: Impure operations with side effects
"""

from abc import ABC, abstractmethod
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
