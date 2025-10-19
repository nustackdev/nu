"""This module defines the *semantic vocabulary* for all nodes in the Redwood Semantics system.

It declares the abstract base classes that express the
core hierarchy of meaning:

    Term
    ├── LValue  → addressable location (Ref)
    └── RValue  → evaluable expression
         ├── Operation → pure (no side effects)
         └── Command   → impure (has side effects)

This layer provides contracts only — no execution logic.
Concrete implementations live in higher layers (structure, behavior, execution).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

# Forward imports within the core subpackage
from redwood.semantics.core.metadata import TermMetadata


T = TypeVar("T")
C = TypeVar("C")  # Context type for evaluation


# ============================================================================
# Abstract Semantic Contracts
# ============================================================================


class Term(ABC):
    """The most abstract semantic unit.

    A Term represents something *meaningful* in the Redwood semantic system —
    either a declarative structure or a runtime expression. Every Term carries
    static metadata describing purity, dependencies, and type expectations.
    """

    meta: TermMetadata

    def __init__(self) -> None:
        self.meta = TermMetadata()

    @abstractmethod
    def evaluate(self, context: C) -> Any:
        """Evaluate this term within a given context.

        Context provides the execution environment (e.g. a tree snapshot, a
        view layer, or a transaction). Pure terms return a value, impure terms
        may mutate state, and addressable terms may return themselves.

        Args:
            context: A runtime context object.

        Returns:
            Evaluation result — depends on subclass semantics.
        """
        ...


# ============================================================================
# LValue — Addressable Terms
# ============================================================================


class LValue(Term):
    """A *locatable* semantic entity — something that can be addressed.

    LValues correspond to the notion of "reference" or "path" — positions in
    a Shape where data resides. They do not inherently perform work; they
    represent the *where* of meaning.
    """

    @abstractmethod
    def resolve(self, context: C) -> tuple[str, ...]:
        """Resolve this reference into a tuple of concrete path segments.

        Implementations may evaluate dynamic indices or keys using the
        provided context.

        Returns:
            A tuple of path segments leading to the addressed slot.
        """
        ...

    @abstractmethod
    def parent(self) -> LValue | None:
        """Return the parent LValue (if any) in the reference chain."""
        ...

    @abstractmethod
    def last_segment(self) -> str | int:
        """Return the last segment name in the reference path."""
        ...


# ============================================================================
# RValue — Evaluable Terms
# ============================================================================


class RValue(Term):
    """An *evaluable* semantic entity — something that produces a value.

    RValues correspond to "expressions" in the Redwood semantics: they may be
    pure (operations) or impure (commands). They represent the *what* of
    meaning — what happens when you evaluate this node.
    """

    @property
    def is_pure(self) -> bool:
        """Whether this RValue has no side effects."""
        return self.meta.is_pure


__all__ = [
    "LValue",
    "RValue",
    "Term",
]
