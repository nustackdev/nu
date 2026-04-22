"""Typed reference to storage location.

Nu                          - the primitive
├── LValue                  - addressable location
│   └── Ref                 - typed pointer to storage location

Core vocabulary:
    resolve(ctx) -> Location    - WHERE is this? (identity/path)
    fetch(ctx) -> T | Sentinel  - WHAT is there? (value extraction)
    open(ctx)                   - Nu evaluator primitive; yields fetched value once
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .nu import LValue
from .types import Mode, Sentinel, T_co


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

    from ..context import Context


__all__ = [
    "Ref",
]


class Ref(LValue[T_co | Sentinel], ABC):
    """Typed pointer to a location. Pure protocol.

    - `resolve()` / `resolve_sync()` build identity/location.
    - `fetch()` / `fetch_sync()` extract the value.
    - `open()` / `open_sync()` are Nu evaluator primitives; yield the fetched value once.
    """

    @abstractmethod
    async def resolve(self, ctx: Context) -> object:
        """Build identity/location for this reference."""
        ...

    @abstractmethod
    async def fetch(self, ctx: Context) -> T_co | Sentinel:
        """Extract value from this location."""
        ...

    def resolve_sync(self, ctx: Context) -> object:
        """Sync counterpart of resolve. Override for SYNC / BOTH Refs."""
        msg = f"{type(self).__name__} has no sync resolve; ASYNC-only Ref"
        raise RuntimeError(msg)

    def fetch_sync(self, ctx: Context) -> T_co | Sentinel:
        """Sync counterpart of fetch. Override for SYNC / BOTH Refs."""
        msg = f"{type(self).__name__} has no sync fetch; ASYNC-only Ref"
        raise RuntimeError(msg)

    async def open(self, ctx: Context) -> AsyncGenerator[T_co | Sentinel, None]:
        """Yield the fetched value once."""
        yield await self.fetch(ctx)

    def open_sync(self, ctx: Context) -> Generator[T_co | Sentinel, None, None]:
        """Yield the fetched value once (sync)."""
        if self.mode is Mode.ASYNC:
            msg = f"{type(self).__name__} is ASYNC-only; cannot run sync"
            raise RuntimeError(msg)
        yield self.fetch_sync(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Refs are always pure. Reading doesn't mutate state."""
        return True
