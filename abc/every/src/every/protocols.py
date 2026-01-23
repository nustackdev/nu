"""User-facing protocols for the every ecosystem.

These protocols define user-friendly interfaces for common operations.
They are separate from the internal Term/Ref protocols.

Protocols:
    Gettable[T]    - objects supporting get(ctx) for value extraction
    Settable[T]    - objects supporting set(ctx, value) for value mutation
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from every.sentinel import Sentinel

    from .term import Context


__all__ = [
    "Gettable",
    "Settable",
]


@runtime_checkable
class Gettable[T](Protocol):
    """Protocol for objects that support value extraction via get().

    This is a user-facing protocol for convenient value access.
    Views, Shapes, and other user-facing APIs implement this.

    For internal Ref protocol, see Ref.fetch().

    Example:
        >>> if isinstance(obj, Gettable):
        ...     value = obj.get(ctx)
    """

    def get(self, ctx: Context) -> T | Sentinel:
        """Get value from this object.

        Args:
            ctx: Execution context

        Returns:
            The value, or Sentinel if absent/invalid
        """
        ...


@runtime_checkable
class Settable[T](Protocol):
    """Protocol for objects that support value mutation via set().

    This is a user-facing protocol for convenient value setting.

    Example:
        >>> if isinstance(obj, Settable):
        ...     obj.set(ctx, new_value)
    """

    def set(self, ctx: Context, value: T) -> None:
        """Set value on this object.

        Args:
            ctx: Execution context
            value: The value to set
        """
        ...
