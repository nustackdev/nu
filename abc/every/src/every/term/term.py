"""Core semantic contracts for EveryShape Shapes.

This module defines the execution model through a minimal type hierarchy:

    Term                        - executable node
    ├── LValue                  - addressable location (has path)
    │   └── Ref                 - typed reference to storage location
    │       ├── ViewRef         - reference to container (dict, list, set)
    │       └── PrimitiveRef    - reference to leaf value (int, str, etc.)
    └── RValue                  - evaluable expression (has children)
        └── Morphism            - transformation (maps inputs to outputs)
            └── NAryMorphism    - morphism with operands and children management
                ├── UnaryMorphism   - single operand (e.g., -x, abs(x))
                ├── BinaryMorphism  - two operands (e.g., x + y, x > y)
                └── TernaryMorphism - three operands (e.g., if a then b else c)

Purity mixins (orthogonal to arity):
    - Operation: pure computation (no side effects)
    - Command: impure mutation (has side effects)

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

Morphism types (pure vs impure):
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
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .context import Context


__all__ = [
    "LValue",
    "RValue",
    "Term",
]


logger = getLogger(__name__)

# =============================================================================
# BASE TERM
# =============================================================================


class Term[ResultT](ABC):
    """Base contract for all executable semantic nodes.

    Everything in the Shape system is a Term:
    - Locations (refs to data)
    - Operations (pure computations)
    - Commands (mutations)

    Terms execute within a Context to produce results.
    Context provides access to the data tree and transaction state.
    """

    @abstractmethod
    def execute(self, context: Context) -> ResultT:
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


class LValue[T](Term[T]):
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
    def resolve(self, context: Context) -> object:
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


# =============================================================================
# RVALUE - EVALUABLE EXPRESSIONS
# =============================================================================


class RValue[ResultT](Term[ResultT]):
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
