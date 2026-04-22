"""StdioRef - references to standard streams.

Three fixed singletons: STDOUT, STDERR, STDIN.
Flat topology - no hierarchy, no paths, just named streams.
"""

from __future__ import annotations

import sys
from typing import IO, TYPE_CHECKING

from nu.terms.ref import Ref


if TYPE_CHECKING:
    from nu.context import Context


__all__ = [
    "STDERR",
    "STDIN",
    "STDOUT",
    "StdioRef",
]


class StdioRef(Ref[IO]):
    """Ref to a standard stream. Three singleton instances.

    StdioRef is a flat, non-hierarchical Ref. No parent chain,
    no address composition. Just a name that maps to a stream.

    Topology: flat. Validates the interaction model works for
    non-KV, stream-based fabrics.
    """

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        """Stream name: 'stdout', 'stderr', or 'stdin'."""
        return self._name

    async def resolve(self, ctx: Context) -> str:
        """Resolve to stream name."""
        return self._name

    def resolve_sync(self, ctx: Context) -> str:
        """Sync counterpart of `resolve`."""
        return self._name

    async def fetch(self, ctx: Context) -> IO:
        """Fetch the stream handle.

        If StdioBackend is bound in Context, uses it.
        Otherwise falls back to sys streams.
        """
        from .backend import StdioBackend

        if ctx.has(StdioBackend):
            return ctx.get(StdioBackend).stream_for(self)
        return getattr(sys, self._name)

    def fetch_sync(self, ctx: Context) -> IO:
        """Sync counterpart of `fetch`."""
        from .backend import StdioBackend

        if ctx.has(StdioBackend):
            return ctx.get(StdioBackend).stream_for(self)
        return getattr(sys, self._name)

    def __repr__(self) -> str:
        return f"StdioRef.{self._name.upper()}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StdioRef):
            return self._name == other._name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(("StdioRef", self._name))


# Singletons
STDOUT = StdioRef("stdout")
STDERR = StdioRef("stderr")
STDIN = StdioRef("stdin")
