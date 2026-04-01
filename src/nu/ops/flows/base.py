"""Flow - control Nu (temporary).

Flows control execution order: sequential, parallel, conditional, looping.
They manage children rather than transforming operands.

Note: Flow as a separate concept is temporary. Will be refined in step 1.4.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from nu.terms import Nu


if TYPE_CHECKING:
    from nu.context import Context


__all__ = [
    "Flow",
]


class Flow(Nu[None], ABC):
    """Control Nu. Manages when children execute.

    Flows define execution order - sequential, parallel,
    conditional, looping. They do not compute values.

    Children can be any Nu (Values, Ops, Refs, Spans, other Flows).
    Default execute() runs children sequentially.
    """

    async def execute(self, ctx: Context) -> None:
        """Execute children sequentially. Override for different ordering."""
        for child in self.children:
            await child.execute(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Flows are impure - they control execution order."""
        return False
