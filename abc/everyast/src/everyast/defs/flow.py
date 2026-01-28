"""Flow -- ordering constraint (1-cell / path)."""

from __future__ import annotations

from abc import ABC

from .exec import Exec


__all__ = [
    "Flow",
]


class Flow(Exec, ABC):
    """Ordering constraint (1-cell). Pure structure.

    Flows define when children execute relative to each other.
    They carry no behavior -- the executor interprets the shape.

    Concrete flows (Seq, Par, Cond, etc.) and algebraic traits
    (Associative, Commutative, etc.) are defined downstream.

    Design rules:
        R2: Flow children can be any Exec.
        S4: Flows own exactly one concern -- ordering (when).
    """

    __slots__ = ()
