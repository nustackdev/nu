"""Term — computation node (0-cell / point).

Terms are executable nodes that produce values. They form
the leaves of the topology tree — the actual computation.

Hierarchy:
    Term[ResultT]           — base: execute(context) -> ResultT
    ├── LValue[T]           — addressable location
    │   └── Ref[T]          — typed reference (see ref.py)
    └── RValue[ResultT]     — evaluable expression
        ├── Value[T]        — typed value holder (see value.py)
        └── Morphism[T]     — transformation (see morphism.py)

Design rules:
    R1: Term children are Terms (closed algebra).
    S4: Terms own exactly one concern — computation (what).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from ..tree import Executable
from .type_vars import T_co


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "LValue",
    "RValue",
    "Term",
]


class Term(Executable["Term"], Generic[T_co], ABC):  # noqa: UP046
    """Base contract for all executable semantic nodes.

    Everything in the topology that computes is a Term:
    - Locations (refs to data)
    - Operations (pure computations)
    - Commands (mutations)

    Terms execute within a Context to produce results.
    Context provides resolved Handles for resource access.

    Inherits from defs.Term which provides:
    - is_self_pure: abstract property (this node only)
    - is_subtree_pure: concrete property (this node + all descendants)
    - children: property returning tuple[Term, ...]
    """

    @abstractmethod
    async def execute(self, ctx: Context) -> T_co:
        """Execute this term within a context.

        Args:
            ctx: Container of resolved handles.

        Returns:
            Term-specific result.
        """
        ...

    @property
    @abstractmethod
    def is_self_pure(self) -> bool:
        """Whether this exact node is pure (no side effects).

        Returns:
            True - if pure, False otherwise
        """
        ...

    @property
    def is_subtree_pure(self) -> bool:
        """Whether this node and its entire subtree are pure.

        Returns:
            True - if self and all descendant Terms are pure
        """
        if not self.is_self_pure:
            return False
        return all(child.is_subtree_pure for child in self._children if isinstance(child, Term))


class LValue(Term[T_co], ABC):
    """Addressable location in the data tree.

    LValues represent positions where data lives.
    They resolve to concrete paths for storage access.
    """


class RValue(Term[T_co], ABC):
    """Evaluable expression that produces a value.

    RValues represent computations — both pure (operations)
    and impure (commands). They compose through children.

    Children are the Terms this expression depends on.
    """
