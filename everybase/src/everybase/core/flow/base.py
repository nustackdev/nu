"""Flow — ordering (when)."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from ..tree import Executable


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Flow",
]


class Flow(Executable[Executable], ABC):
    """Ordering node. Controls when children execute.

    Flows define execution order — sequential, parallel,
    conditional, looping. They do not compute values.

    Children can be Terms, Flows, or Spans.
    Default execute() runs children sequentially.
    """

    async def execute(self, ctx: Context) -> None:
        """Execute children sequentially. Override for different ordering."""
        for child in self.children:
            await child.execute(ctx)
