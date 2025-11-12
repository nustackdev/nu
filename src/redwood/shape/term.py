"""Core semantic contracts for Redwood Shapes.

This module defines the execution model through a minimal type hierarchy:

    Term                    - executable node
    ├── LValue              - addressable location (has path)
    │   └── Ref[T]          - typed reference
    └── RValue              - evaluable expression (has children)
        ├── Operation[T]    - pure computation → T
        └── Command[T]      - impure mutation → T

Design principles:
    - Minimal contracts: only essential methods
    - Uniform composition: everything uses children tuple
    - Type propagation: generic T flows through chains
    - Purity explicit: is_pure property on RValue

LValue vs RValue:
    LValue = location where data lives (can resolve to path)
    RValue = expression that produces value (can execute)

    Market.price            → LValue (location)
    Market.price.get()      → RValue (reads from location)
    price + 100             → RValue (computes)
    price.set(150)          → RValue (writes to location)

Pure vs Impure:
    Operation = deterministic, no side effects, cacheable
    Command   = modifies state, transactional, explicit effects

Both return values - the split is about side effects, not return types.

Example usage:
>>> # Define location
>>> price_ref: Ref[float] = Market.orders["AAPL"].price

>>> # Create pure operation
>>> read_op: Operation[float] = price_ref.get()

>>> # Create impure command
>>> write_cmd: Command[float] = price_ref.set(150.0)

>>> # Execute in context
>>> value = read_op.execute(ctx)
>>> result = write_cmd.execute(ctx)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .core.ergonomics import ErgonomicsMixin


if TYPE_CHECKING:
    from redwood.loc import path

    from .context import Context


__all__ = [
    "Command",
    "LValue",
    "Operation",
    "RValue",
    "Ref",
    "Term",
]


# =============================================================================
# BASE TERM
# =============================================================================


class Term(ABC):
    """Base contract for all executable semantic nodes.

    Everything in the Shape system is a Term:
    - Locations (refs to data)
    - Operations (pure computations)
    - Commands (mutations)

    Terms execute within a Context to produce results.
    Context provides access to the data tree and transaction state.
    """

    @abstractmethod
    def execute(self, context: Context) -> object:
        """Execute this term within a context.

        Semantics depend on term type:
        - Ref: returns itself (locations don't compute)
        - Operation: returns computed value
        - Command: performs mutation, returns result

        Args:
            context: Execution environment (tree + storage context)

        Returns:
            Term-specific result
        """
        ...


# =============================================================================
# LVALUE - ADDRESSABLE LOCATIONS
# =============================================================================


class LValue(Term):
    """Addressable location in the data tree.

    LValues represent positions where data lives.
    They are resolved to concrete paths for storage access.

    Key operations:
    - resolve(): Get path segments to this location
    - parent(): Navigate up the hierarchy
    - last_segment(): Get final segment

    LValues form navigation chains:
        Market.orders["AAPL"].price
        └─────┬─────┘ └──┬──┘ └─┬─┘
           parent    parent  self

    Concrete implementations (in rwstd):
    - ValueRef: primitive values (int, str, float)
    - ShapeRef: nested structures
    - MapRef: mapping containers
    - MapItemRef: specific map entries
    """

    @abstractmethod
    def resolve(self, context: Context) -> path.Path:
        """Resolve to concrete Path.

        Args:
            context: Context for evaluating dynamic components

        Returns:
            Path to the location ((address, type), ...)

        Example:
            >>> Market.orders["AAPL"].resolve(ctx)
            (("orders", DictView), ("AAPL", DictView),)
            >>> Market.orders["AAPL"].price.resolve(ctx)
            (("orders", DictView), ("AAPL", DictView), ("price", float))
        """
        ...

    @abstractmethod
    def parent(self) -> LValue | None:
        """Get parent location in the navigation chain.

        Used for path construction and hierarchy traversal.
        Root locations return None.

        Returns:
            Parent LValue, or None if this is root
        """
        ...

    @abstractmethod
    def last_segment(self) -> path.PathSegment:
        """Get the final segment in this location's path.

        Returns:
            Final path segment

        Example:
            >>> Market.orders["AAPL"].price.last_segment()
            ("price", float))
        """
        ...


# =============================================================================
# RVALUE - EVALUABLE EXPRESSIONS
# =============================================================================


class RValue[T](Term, ErgonomicsMixin[T]):
    """Evaluable expression that produces a value.

    RValues represent computations - both pure (operations) and
    impure (commands). They compose through a children tuple.

    Key properties:
    - children: Tuple of dependent terms
    - is_pure: Whether this has side effects

    Composition pattern:
        expr = BinaryOp("add",
            left=GetOp(price_ref),
            right=LiteralValue(100)
        )
        expr.children = (GetOp(...), LiteralValue(...))

    Children can be any Term:
    - Other RValues (nested expressions)
    - LValues (refs for read/write operations)

    Concrete implementations (in rwstd):
    - Operations: GetOp, BinaryOp, UnaryOp, LiteralValue
    - Commands: SetCmd, DeleteCmd, UpdateCmd
    """

    children: tuple[Term, ...]
    """Terms this expression depends on.

    Used for:
    - Composition: building expression trees
    - Traversal: walking the AST
    - Analysis: determining purity, dependencies

    Empty tuple for leaf terms (literals, some refs).
    """

    @property
    @abstractmethod
    def is_pure(self) -> bool:
        """Whether this expression has side effects.

        Pure expressions (Operations):
        - Deterministic: same input → same output
        - No mutations: doesn't change tree state
        - Cacheable: can memoize results
        - Reorderable: execution order doesn't matter

        Impure expressions (Commands):
        - Side effects: modifies tree state
        - Order-dependent: sequence matters
        - Transactional: needs transaction context

        Returns:
            True if pure (no side effects), False if impure
        """
        ...


# =============================================================================
# OPERATION - PURE COMPUTATIONS
# =============================================================================


class Operation[T](RValue[T]):
    """Pure computation that returns a value of type T.

    Operations are deterministic expressions with no side effects:
    - Reading values from tree
    - Arithmetic and logical computations
    - Comparisons and transformations

    Purity is compositional:
    - Operation is pure if all RValue children are pure
    - LValue children don't affect purity (they're locations)

    Generic type T specifies return type:
        Operation[float] → returns float
        Operation[bool]  → returns bool
        Operation[list[str]] → returns list of strings

    Examples (concrete implementations in rwstd):
        GetOp(price_ref)              → Operation[float]
        BinaryOp("gt", price, 100)    → Operation[bool]
        UnaryOp("neg", balance)       → Operation[float]
    """

    @property
    def is_pure(self) -> bool:
        """Operations are pure if all RValue children are pure.

        LValue children (refs) don't affect purity - they're just locations.
        Only RValue children can introduce impurity.

        Returns:
            True if all RValue children are pure
        """
        return all(child.is_pure for child in self.children if isinstance(child, RValue))

    @abstractmethod
    def execute(self, context: Context) -> T:
        """Execute pure computation and return typed result.

        Typical execution pattern:
        1. Evaluate all children
        2. Apply operation logic
        3. Return typed result

        Args:
            context: Execution environment

        Returns:
            Computed value of type T
        """
        ...


# =============================================================================
# COMMAND - IMPURE MUTATIONS
# =============================================================================


class Command[T](RValue[T]):
    """Impure mutation that returns a result of type T.

    Commands modify tree state with explicit side effects:
    - Writing values
    - Deleting entries
    - Updating based on current state

    Commands always return values:
    - Enables composition: outer.set(inner.set(x))
    - Useful patterns: "write and return", "delete and return old"
    - Natural chaining: price.set(100).get()

    Must execute in transactional context for atomicity.

    Examples (concrete implementations in rwstd):
        SetCmd(price_ref, 150.0)           → Command[float]
        DeleteCmd(orders_ref, "AAPL")      → Command[Order]
        UpdateCmd(balance_ref, lambda x: x * 1.1) → Command[float]
    """

    @property
    def is_pure(self) -> bool:
        """Commands are always impure by definition.

        Returns:
            False - commands always have side effects
        """
        return False

    @abstractmethod
    def execute(self, context: Context) -> T:
        """Execute mutation and return result.

        Typical execution pattern:
        1. Resolve target location
        2. Perform mutation (write/delete/update)
        3. Return result (written value, old value, etc.)

        Must run within transaction context:
            with storage.transaction() as tx:
                ctx = Context(root_view, tx)
                result = command.execute(ctx)

        Args:
            context: Execution environment with transaction

        Returns:
            Result of type T (often the written/deleted value)
        """
        ...


# =============================================================================
# REF - TYPED REFERENCES
# =============================================================================


class Ref[T](LValue, ABC):
    """Typed reference to a location in the tree.

    Combines addressability (LValue) with type information.
    Refs are both locations AND terms (dual nature):

    As LValue:
    - Can resolve to paths
    - Can navigate to parent
    - Can get last segment

    As Term:
    - Can execute (returns self)
    - Can be used in children tuples

    Generic type T specifies value type at this location:
        Ref[float] → location holding float
        Ref[str]   → location holding string
        Ref[Order] → location holding Order shape

    Concrete implementations (in rwstd):
        ValueRef[T]     - primitive values
        ShapeRef[T]     - nested structures
        MapRef[K,V]     - mapping containers
        MapItemRef[T]   - specific map entries

    Implementations determine:
    - Storage strategy (caching, lazy evaluation)
    - Navigation behavior (nested field access)
    - Available operations (get/set for values, keys/items for maps)
    """

    def execute(self, context: Context) -> Ref[T]:
        """Execute returns self - refs are locations, not computations.

        This enables refs to be used uniformly in expression trees
        while maintaining their identity as locations.

        Args:
            context: Unused - refs don't compute

        Returns:
            Self (the location reference)
        """
        return self
