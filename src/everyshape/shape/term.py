"""Core semantic contracts for EveryShape Shapes.

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
from logging import getLogger
from typing import TYPE_CHECKING, Generic, TypeVar

from everyshape.loc import path

from .context import ContextProtocol


if TYPE_CHECKING:
    from everyshape.types import Value
    from everyshape.view import View

    from .shape import Shape


__all__ = [
    "Command",
    "LValue",
    "Operation",
    "PrimitiveRef",
    "RValue",
    "Ref",
    "Term",
    "ViewRef",
]

ViewT_co = TypeVar("ViewT_co", covariant=True, bound="View")
ContextT = TypeVar("ContextT", bound=ContextProtocol)


logger = getLogger(__name__)

# =============================================================================
# BASE TERM
# =============================================================================


class Term[ResultT, ContextT: ContextProtocol](ABC):
    """Base contract for all executable semantic nodes.

    Everything in the Shape system is a Term:
    - Locations (refs to data)
    - Operations (pure computations)
    - Commands (mutations)

    Terms execute within a Context to produce results.
    Context provides access to the data tree and transaction state.
    """

    @abstractmethod
    def execute(self, context: ContextT) -> ResultT:
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

    @property
    @abstractmethod
    def is_pure(self) -> bool:
        """Whether this term has side effects.

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
# LVALUE - ADDRESSABLE LOCATIONS
# =============================================================================


class LValue[PathTypeT: path.Path, ContextT: ContextProtocol](Term[None, ContextT]):
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

    Concrete implementations (see in standard library or ecosystem repo):
    - ValueRef: primitive values (int, str, float)
    - ShapeRef: nested structures
    - MapRef: mapping containers
    - MapItemRef: specific map entries
    """

    @abstractmethod
    def resolve(self, context: ContextT) -> PathTypeT:
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

    def execute(self, context: ContextT) -> None:
        """Execute does not make sense for LValues (LValues are locations not computations).

        Args:
            context: Unused - LValues don't compute

        Raises:
            NotImplementedErrors
        """
        raise NotImplementedError("LValues are not executables.")


# =============================================================================
# RVALUE - EVALUABLE EXPRESSIONS
# =============================================================================


class RValue[ResultT, ContextT: ContextProtocol](Term[ResultT, ContextT]):
    """Evaluable expression that produces a value.

    RValues represent computations - both pure (operations) and
    impure (commands). They compose through a children tuple.

    Key properties:
    - children: Tuple of dependent terms
    - is_pure: Whether this has side effects

    Composition pattern:
        # Via factory (backward compatible)
        expr = BinaryOp("add",
            left=GetOp(price_ref),
            right=LiteralValue(100)
        )
        # Or via atomic classes (preferred)
        expr = AddOp(GetOp(price_ref), LiteralValue(100))
        expr.children = (GetOp(...), LiteralValue(...))

    Children can be any Term:
    - Other RValues (nested expressions)
    - LValues (refs for read/write operations)

    Concrete implementations (see in standard library or ecosystem repo):
    - Operations: GetOp, AddOp, SubOp, MulOp, DivOp, etc., UnaryOp, LiteralValue
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


# =============================================================================
# OPERATION - PURE COMPUTATIONS
# =============================================================================


class Operation[OperationResultT, ContextT: ContextProtocol](RValue[OperationResultT, ContextT]):
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

    Examples (concrete implementations see in standard library or ecosystem repo):
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
    def execute(self, context: ContextT) -> OperationResultT:
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


class Command[CommandResultT, ContextT: ContextProtocol](RValue[CommandResultT, ContextT]):
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

    Examples (concrete implementations see in standard library or ecosystem repo):
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
    def execute(self, context: ContextT) -> CommandResultT:
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


class Ref[PathTypeT: path.Path, ContextT: ContextProtocol](LValue[PathTypeT, ContextT], ABC):
    """Typed reference to a location in the tree.

    Combines addressability (LValue) with type information.
    Refs are both locations AND terms (dual nature):

    As Ref:
    - Can resolve to paths
    - Can navigate to parent

    As Term:
    - Can execute (returns self)
    - Can be used in children tuples

    Generic type T specifies value type at this location:
        Ref[float] → location holding float
        Ref[str]   → location holding string
        Ref[Order] → location holding Order shape

    Concrete implementations (see in standard library or ecosystem repo):
        ValueRef[T]     - primitive values
        ShapeRef[T]     - nested structures
        MapRef[K,V]     - mapping containers
        MapItemRef[T]   - specific map entries

    Implementations determine:
    - Storage strategy (caching, lazy evaluation)
    - Navigation behavior (nested field access)
    - Available operations (get/set for values, keys/items for maps)
    """

    def __init__(self, parent_ref: Ref | None, owner_shape: type[Shape] | None) -> None:
        """Init Ref."""
        self.parent_ref = parent_ref
        self.owner_shape = owner_shape

    @property
    def is_pure(self) -> bool:
        """Refs are always pure.

        Returns:
            True - refs never have side effects
        """
        return True

    @property
    def parent(self) -> Ref | None:
        """Get parent location in the navigation chain.

        Used for path construction and hierarchy traversal.
        Root locations return None.

        Returns:
            Parent Ref, or None if this is root
        """
        return self.parent_ref

    def get_owner_shape(self) -> type[Shape] | None:
        """Get the Shape class this Ref was created by."""
        if self.owner_shape is not None:
            return self.owner_shape

        if self.parent is not None:
            return self.parent.owner_shape

        return None

    def get_root_shape(self) -> type[Shape] | None:
        """Get the Shape class this Ref was originated from."""
        if self.parent is not None:
            return self.parent.get_root_shape()

        if self.owner_shape is not None:
            return self.owner_shape

        return None


class ViewRef(Generic[ViewT_co, ContextT], Ref[path.PathToView, ContextT], ABC):  # noqa: UP046
    """Ref that points to a View (container in the tree)."""

    def __init__(
        self,
        address: path.PathAddress | RValue,
        view_type: type[ViewT_co],
        parent_ref: Ref | None = None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Init ViewRef."""
        super().__init__(parent_ref, owner_shape)

        self.address = address
        self.view_type = view_type

    def resolve(self, context: ContextT) -> path.PathToView:
        """Resolve to path ending at this shape's view.

        Args:
            context: Execution context

        Returns:
            Path ending with view segment
        """
        if isinstance(self.address, RValue):
            address = self.address.execute(context)
        else:
            address = self.address

        if self.parent_ref is None:
            resolved_path = ((address, self.view_type),)
        else:
            parent_path = self.parent_ref.resolve(context)
            resolved_path = (*parent_path, (address, self.view_type))

        logger.debug(
            "ViewRef resolved",
            extra={
                "address": address,
                "view_type": self.view_type.__name__,
                "has_parent": self.parent_ref is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path

    def __repr__(self) -> str:
        """ViewRef representation in machine-friendly format."""
        if self.parent_ref:
            return f"<ViewRef: {self.parent_ref!r} -> {self.address!r}>"
        return f"<ViewRef: {self.address!r}>"

    def __str__(self) -> str:
        """ViewRef representation in human-friendly format."""
        if self.parent_ref:
            return f"ViewRef({self.parent_ref!s} -> {self.address!s})"
        return f"ViewRef({self.address!s})"


class PrimitiveRef[T: Value, ContextT: ContextProtocol](Ref[path.PathToValue, ContextT], ABC):
    """Ref that points to a primtive value in the tree (leaf node)."""

    def __init__(
        self,
        address: path.PathAddress | RValue,
        value_type: type[T],
        parent_ref: Ref | None,
        owner_shape: type[Shape] | None = None,
    ) -> None:
        """Init ValueRef."""
        super().__init__(parent_ref, owner_shape)
        self.address = address
        self.value_type = value_type

    def resolve(self, context: ContextT) -> path.PathToValue:
        """Resolve to complete path ending at value.

        Args:
            context: Execution context

        Returns:
            Path ending with value segment
        """
        if isinstance(self.address, RValue):
            address = self.address.execute(context)
        else:
            address = self.address

        if self.parent_ref is None:
            resolved_path = ((self.address, self.value_type),)
        else:
            parent_path = self.parent_ref.resolve(context)
            resolved_path = (*parent_path, (address, self.value_type))

        logger.debug(
            "PrimitiveRef resolved",
            extra={
                "address": address,
                "value_type": type(self.value_type).__name__,
                "has_parent": self.parent_ref is not None,
                "resolved_path": resolved_path,
            },
        )
        return resolved_path

    def __repr__(self) -> str:
        """PrimitiveRef representation in machine-friendly format."""
        if self.parent_ref:
            return f"<PrimitiveRef: {self.parent_ref!r} -> {self.address!r}>"
        return f"<PrimitiveRef: {self.address!r}>"

    def __str__(self) -> str:
        """PrimitiveRef representation in human-friendly format."""
        if self.parent_ref:
            return f"PrimitiveRef({self.parent_ref!s} -> {self.address!s})"
        return f"PrimitiveRef({self.address!s})"
