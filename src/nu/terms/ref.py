"""Typed reference to storage location.

Nu                          - the primitive
├── LValue                  - addressable location
│   └── Ref                 - typed pointer to storage location

Core vocabulary:
    resolve(ctx) -> Location    - WHERE is this? (identity/path)
    fetch(ctx) -> T | Sentinel  - WHAT is there? (value extraction)
    execute(ctx)                - Nu interface, delegates to fetch()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from .nu import LValue
from .sentinel import Sentinel
from .type_vars import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from ..context import Context


__all__ = [
    "Ref",
]


class Ref(LValue[T_co | Sentinel], ABC):
    """Typed pointer to a location. Pure protocol.

    Ref is the minimal contract for typed references:
    - resolve(): build identity/location
    - fetch(): extract value
    - execute(): Nu compatibility (delegates to fetch)

    No parent. No shape. No substrate assumptions.
    """

    @abstractmethod
    async def resolve(self, ctx: Context) -> object:
        """Build identity/location for this reference.

        Returns a substrate-specific location identifier.
        For path-based substrates, this builds the path.
        For simple substrates, may return minimal identifier.

        Args:
            ctx: Execution context

        Returns:
            Location identifier (substrate-specific)
        """
        ...

    @abstractmethod
    async def fetch(self, ctx: Context) -> T_co | Sentinel:
        """Extract value from this location.

        The core operation of a Ref - retrieve the value
        from wherever it lives (memory, storage, network, etc.).

        Args:
            ctx: Execution context providing storage access

        Returns:
            The value at this location, or Sentinel if absent/invalid
        """
        ...

    async def execute(self, ctx: Context) -> T_co | Sentinel:
        """Execute this ref by fetching its value."""
        return await self.fetch(ctx)

    @asynccontextmanager
    async def open(self, ctx: Context) -> AsyncIterator[T_co | Sentinel]:
        """Open this ref: yield fetched value. Overrides TypedNu.open() in MRO."""
        yield await self.fetch(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Refs are always pure. Reading doesn't mutate state."""
        return True
