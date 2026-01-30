"""Typed reference to storage location.

Term                        - executable node
├── LValue                  - addressable location (has path)
│   └── Ref                 - typed reference to storage location

Ref is the pure protocol for typed references. No substrate assumptions.
Substrates (Python memory, PV storage, etc.) extend this with their
own storage implementations.

Core vocabulary:
    resolve(ctx) → Location    - WHERE is this? (identity/path)
    fetch(ctx) → T | Sentinel  - WHAT is there? (value extraction)
    execute(ctx)               - Term interface, delegates to fetch()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .sentinel import Sentinel
from .term import LValue


if TYPE_CHECKING:
    from everyabc.context import Context


__all__ = [
    "Ref",
]


class Ref[T](LValue[T | Sentinel], ABC):
    """Typed reference to a location. Pure protocol.

    Ref is the minimal contract for typed references:
    - resolve(): build identity/location
    - fetch(): extract value
    - execute(): Term compatibility (delegates to fetch)

    No parent. No shape. No substrate assumptions.
    Substrates add their own storage mechanisms.

    Generic type T specifies value type at this location:
        Ref[float] → location holding float
        Ref[str]   → location holding string
        Ref[Order] → location holding Order shape
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
    async def fetch(self, ctx: Context) -> T | Sentinel:
        """Extract value from this location.

        The core operation of a Ref - retrieve the value
        from wherever it lives (memory, storage, network, etc.).

        Args:
            ctx: Execution context providing storage access

        Returns:
            The value at this location, or Sentinel if absent/invalid
        """
        ...

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Execute this ref by fetching its value.

        Term interface compatibility. For Refs, execution means
        fetching the value from the location.

        Args:
            ctx: Execution context

        Returns:
            The fetched value
        """
        return await self.fetch(ctx)

    @property
    def is_self_pure(self) -> bool:
        """Refs are always pure.

        Reading from a location doesn't mutate state.

        Returns:
            True - refs never have side effects
        """
        return True
