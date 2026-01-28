"""Term -- computation node (0-cell / point)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .exec import Exec


__all__ = [
    "Term",
]


class Term(Exec, ABC):
    """Computation node (0-cell). Structural contract.

    Terms form a closed algebra: children of a Term are Terms (R1).
    Purity marks whether a term is side-effect-free.

    Design rules:
        R1: Term children are Terms (closed algebra).
        S4: Terms own exactly one concern -- computation (what).
    """

    __slots__ = ()

    @property
    @abstractmethod
    def is_pure(self) -> bool:
        """Whether this term is side-effect-free.

        Pure: deterministic, cacheable, reorderable.
        Impure: side effects, order-dependent.
        """
        ...

    @property
    def children(self) -> tuple[Term, ...]:
        """R1: Term children are Terms. Default: leaf."""
        return ()
