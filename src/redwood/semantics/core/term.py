"""Core term contracts for Redwood Semantics.

This module defines the semantic vocabulary - the abstract base classes
that express the hierarchy of meaning in the Redwood system:

    Term (abstract)
    ├── LValue → addressable location (references)
    └── RValue → evaluable expression
         ├── Operation → pure (reads, computations)
         └── Command → impure (writes, mutations)

Contracts:
    - Term: Base for all semantic nodes, defines execute() contract
    - LValue: Addressable locations, defines resolve() / parent() / last_segment()
    - RValue: Evaluable expressions, defines is_pure property

This is the CONTRACT layer - no implementations here, just interfaces.
Concrete implementations live in higher layers:
    - behavior/refs.py → LValue implementations
    - behavior/operations.py → pure RValue implementations
    - behavior/commands.py → impure RValue implementations

Design Philosophy:
    - Minimal contracts (only essential methods)
    - Clear separation (location vs computation)

The term hierarchy mirrors classic L-value / R-value semantics from
programming language theory:
    - LValue = something that can appear on left of assignment (has location)
    - RValue = something that can appear on right of assignment (produces value)

Example conceptual mapping:
    Market.orders["AAPL"].price       → LValue (location)
    Market.orders["AAPL"].price.get() → RValue (reads from location)
    price > 100                       → RValue (compares values)
    price.set(150)                    → RValue (writes to location, impure)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from redwood.abc import KeyComponent, TupleKey

    from ..types import Context


# ============================================================================
# Base Term
# ============================================================================


class Term(ABC):
    """Abstract base for all semantic nodes.

    Terms represent meaningful units in the Redwood semantics - either
    addressable locations or evaluable expressions.
    """

    @abstractmethod
    def execute(self, context: Context) -> object:
        """Execute this term within a context.

        Args:
            context: Execution environment (tree + storage context)

        Returns:
            Execution result - depends on term type
        """
        ...


# ============================================================================
# LValue - Addressable Terms
# ============================================================================


class LValue(Term):
    """Addressable location in tree.

    LValues represent references to positions where data lives.
    They can be resolved to concrete paths.
    """

    @abstractmethod
    def resolve(self, context: Context) -> TupleKey:
        """Resolve to concrete path segments.

        For static refs: returns cached path
        For dynamic refs: evaluates expressions to compute path

        Args:
            context: Context for evaluating dynamic components

        Returns:
            Tuple of path segments
        """
        ...

    @abstractmethod
    def parent(self) -> LValue | None:
        """Return parent reference in navigation chain.

        Returns:
            Parent LValue, or None if root
        """
        ...

    @abstractmethod
    def last_segment(self) -> KeyComponent:
        """Return the last segment in the path.

        Returns:
            Final key or index as a path segment
        """
        ...


# ============================================================================
# RValue - Evaluable Terms
# ============================================================================


class RValue(Term):
    """Evaluable expression that produces a value.

    RValues represent computations - either pure (operations) or
    impure (commands).
    """

    @property
    @abstractmethod
    def is_pure(self) -> bool:
        """Whether this expression has side effects.

        Returns:
            True if pure (no side effects), False if impure
        """
        ...


__all__ = [
    "LValue",
    "RValue",
    "Term",
]
