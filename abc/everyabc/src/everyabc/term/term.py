"""Term — computation node (0-cell / point).

Terms are executable nodes that produce values. They form
the leaves of the topology tree — the actual computation.

Hierarchy:
    Term[ResultT]           — base: execute(context) -> ResultT
    ├── LValue[T]           — addressable location (has resolve)
    │   └── Ref[T]          — typed reference (see ref.py)
    └── RValue[ResultT]     — evaluable expression
        └── Morphism[T]     — transformation (see morphism.py)

Design rules:
    R1: Term children are Terms (closed algebra).
    S4: Terms own exactly one concern — computation (what).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from everyabc.tree import Exec


if TYPE_CHECKING:
    from everyabc.context import Context


__all__ = [
    "LValue",
    "RValue",
    "Term",
]


class Term[ResultT](Exec["Term"], ABC):
    """Base contract for all executable semantic nodes.

    Everything in the topology that computes is a Term:
    - Locations (refs to data)
    - Operations (pure computations)
    - Commands (mutations)

    Terms execute within a Context to produce results.
    Context provides resolved Handles for resource access.

    Inherits from defs.Term which provides:
    - is_pure: abstract property
    - children: property returning tuple[Term, ...]
    """

    @abstractmethod
    def execute(self, context: Context) -> ResultT:
        """Execute this term within a context.

        Args:
            context: Container of resolved handles.

        Returns:
            Term-specific result.
        """
        ...


class LValue[T](Term[T]):
    """Addressable location in the data tree.

    LValues represent positions where data lives.
    They resolve to concrete paths for storage access.
    """

    @abstractmethod
    def resolve(self, context: Context) -> object:
        """Resolve to concrete location identifier.

        Returns a substrate-specific location identifier.
        """
        ...


class RValue[ResultT](Term[ResultT]):
    """Evaluable expression that produces a value.

    RValues represent computations — both pure (operations)
    and impure (commands). They compose through children.

    Children are the Terms this expression depends on.
    """
