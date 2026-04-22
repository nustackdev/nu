"""Command - imperative mutation. Contains WRITE in subtree. Yields nothing.

Taxonomy under Interaction:

    Command                   yields nothing; effect set contains WRITE
    ├── Atomic                terminal mutation; no inner Command. Hook: run / run_sync
    └── Flow                  orchestrates inner Commands. Override open / open_sync

Atomic is the leaf pattern: override `run` / `run_sync`; base wraps to 0-yield.
Flow is the orchestrator pattern: override `open` / `open_sync` directly;
`run` is left as the default raise (Flow doesn't use it).
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
    """0-yield Interaction. Role marker.

    No abstract hook on the base: Atomic subclasses authoring via `run`
    declare their own abstract; Flow subclasses override `open` directly
    and leave `run` as the default raise.
    """

    async def run(self, ctx: Context) -> None:
        """Async side effect. Default raises; override or use open."""
        msg = f"{type(self).__name__} has no run; override run or open"
        raise NotImplementedError(msg)

    def run_sync(self, ctx: Context) -> None:
        """Sync side effect. Default raises; override or use open_sync."""
        msg = f"{type(self).__name__} has no run_sync; override run_sync or open_sync"
        raise NotImplementedError(msg)

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
    """Terminal mutation. Leaf in the Command tree.

    Override `run(ctx)` for async or `run_sync(ctx)` for sync. No inner
    Command; children are all Queries (value to write, target Ref, etc).
    """

    @abstractmethod
    async def run(self, ctx: Context) -> None:
        """Perform the mutation. Called once."""
        ...


class Flow(Command, ABC):
    """Orchestrates inner Commands. Override `open` / `open_sync`.

    Children include Commands (body, branches) and Queries (control
    values). Flow doesn't use `run`; override `open` directly.
    """
