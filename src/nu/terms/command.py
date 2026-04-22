"""Command - imperative mutation. Contains WRITE in subtree. Yields nothing.

Taxonomy under Interaction:

    Command                   yields nothing; effect set contains WRITE
    ├── Atomic                terminal mutation; no inner Command (children all Query)
    └── Flow                  orchestrates inner Commands (body/branches Cmd, control values Q)

Atomic and Flow are markers. Structural invariants (Atomic has no Command
child; Flow has >= 1 Command descendant) are documented and can be checked
at init under a debug flag - not enforced by default.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .interaction import Interaction
from .types import Mode


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context


__all__ = [
    "Atomic",
    "Command",
    "Flow",
]


class Command(Interaction, ABC):
    """0-yield Interaction. Hook: run(ctx) / arun(ctx) returning None.

    Use for Interactions that transform Γ (write through a Ref, call a
    fabric side-effect) and return nothing to the stream.
    """

    @abstractmethod
    async def run(self, ctx: Context) -> None:
        """Perform the side effect. No return value."""
        ...

    def run_sync(self, ctx: Context) -> None:
        """Sync side effect. Override for SYNC / BOTH Commands; default raises."""
        msg = f"{type(self).__name__} has no run_sync; ASYNC-only Command"
        raise RuntimeError(msg)

    async def open(self, ctx: Context) -> AsyncGenerator[None, None]:
        await self.run(ctx)
        return
        yield  # unreachable; marks this as a generator

    def open_sync(self, ctx: Context) -> Generator[None, None, None]:
        if self.mode is Mode.ASYNC:
            msg = f"{type(self).__name__} is ASYNC-only; cannot run sync"
            raise RuntimeError(msg)
        self.run_sync(ctx)
        return
        yield  # unreachable


class Atomic(Command, ABC):
    """Terminal mutation. No inner Command.

    Marker. Children are all Queries (value to write, target Ref, etc).
    Structural invariant: no Command anywhere in the children. Not enforced
    by default.
    """


class Flow(Command, ABC):
    """Orchestrates inner Commands. Control flow over mutations.

    Marker. Children include Commands (body, branches) and Queries (control
    values: condition, items, retry count, etc). Structural invariant: at
    least one Command in the subtree (a Flow around no mutation is a
    control-flow skeleton around nothing). Not enforced by default.
    """
