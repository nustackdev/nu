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
from .sentinel import Sentinel
from .type_vars import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ..context import Context


__all__ = [
    "Ref",
]


class Ref(LValue[T_co | Sentinel], ABC):
    """Typed pointer to a location. Pure protocol.

    - `resolve()` builds identity/location.
    - `fetch()` extracts the value.
    - `open()` is the Nu evaluator primitive; yields the fetched value once.
    """

    @abstractmethod
    async def resolve(self, ctx: Context) -> object:
        """Build identity/location for this reference."""
        ...

    @abstractmethod
    async def fetch(self, ctx: Context) -> T_co | Sentinel:
        """Extract value from this location."""
        ...

    async def open(self, ctx: Context) -> AsyncGenerator[T_co | Sentinel, None]:
        """Yield the fetched value once."""
        yield await self.fetch(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Refs are always pure. Reading doesn't mutate state."""
        return True
