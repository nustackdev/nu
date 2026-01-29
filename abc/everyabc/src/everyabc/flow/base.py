"""Flow -- ordering constraint (1-cell / path)."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from everyabc.tree import Exec


if TYPE_CHECKING:
    from everyabc.context import Context


__all__ = [
    "Flow",
]


class Flow(Exec[Exec], ABC):
    """Ordering constraint (1-cell). Controls child execution.

    Flows define when children execute relative to each other.
    Default execute() runs children sequentially.

    Concrete flows (Seq, Par, Cond, etc.) override execute()
    to provide specific ordering semantics.

    Design rules:
        R2: Flow children can be any Exec.
        S4: Flows own exactly one concern -- ordering (when).
    """

    __slots__ = ()

    def execute(self, ctx: Context) -> None:
        """Execute children sequentially. Override for different ordering."""
        for child in self.children:
            child.execute(ctx)
