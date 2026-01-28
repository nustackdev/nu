"""Protocols for the everyabc ecosystem.

Fetchable[T]  — objects supporting fetch(ctx) for value extraction
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from everyabc.context import Context

    from .sentinel import Sentinel


__all__ = [
    "Fetchable",
]


@runtime_checkable
class Fetchable[T](Protocol):
    """Protocol for objects that support value extraction via fetch().

    Used by morphisms to resolve operands that aren't Terms but
    can provide values when given a context.

    Example:
        >>> if isinstance(obj, Fetchable):
        ...     value = obj.fetch(ctx)
    """

    def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch value from this object.

        Args:
            ctx: Execution context

        Returns:
            The value, or Sentinel if absent/invalid
        """
        ...
