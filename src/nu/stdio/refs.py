"""StdioRef - references to standard streams.

Three fixed singletons: STDOUT, STDERR, STDIN.
"""

from __future__ import annotations

import sys
from typing import IO, ClassVar

from nu.terms.ref import Ref
from nu.terms.types import Mode


__all__ = [
    "STDERR",
    "STDIN",
    "STDOUT",
    "StdioRef",
]


class StdioRef(Ref[IO]):
    """Ref to a standard stream. Three singleton instances."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def resolve(self, ctx: object) -> str:
        return self._name

    async def aresolve(self, ctx: object) -> str:
        return self._name

    def fetch(self, ctx: object) -> IO:
        from .backend import StdioBackend

        if ctx.has(StdioBackend):
            return ctx.get(StdioBackend).stream_for(self)
        return getattr(sys, self._name)

    async def afetch(self, ctx: object) -> IO:
        from .backend import StdioBackend

        if ctx.has(StdioBackend):
            return ctx.get(StdioBackend).stream_for(self)
        return getattr(sys, self._name)

    def eval(self, ctx: object) -> IO:
        return self.fetch(ctx)

    async def aeval(self, ctx: object) -> IO:
        return await self.afetch(ctx)

    def __repr__(self) -> str:
        return f"StdioRef.{self._name.upper()}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StdioRef):
            return self._name == other._name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(("StdioRef", self._name))


STDOUT = StdioRef("stdout")
STDERR = StdioRef("stderr")
STDIN = StdioRef("stdin")
