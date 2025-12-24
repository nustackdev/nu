"""Base RValue implementation.

This module defines the base class for concrete RValue implementations.
RValueBase provides the foundation for building type-specific values
that represent already computed/available values in the DSL.

Key difference from LValues:
- RValues are ALREADY COMPUTED values available in memory
- LValues are LOCATIONS in storage that need to be accessed

RValues compose through the Term system's children tuple and
support operator overloading via ergonomics mixins.
"""

from __future__ import annotations

from abc import ABC

from ..context import ContextProtocol
from ..term import Operation


__all__ = [
    "LiteralBase",
]


class LiteralBase[T, ContextT: ContextProtocol](Operation[T, ContextT], ABC):
    """Base class for literal (constant) RValues.

    Literal values wrap native Python values directly and don't
    require any computation to produce their value.

    Type Parameters:
        T: The native Python type this literal wraps
        ContextT: The execution context type

    Example:
        >>> lit = IntLiteral(42)
        >>> lit.unwrap()  # Returns 42
        >>> lit.execute(ctx)  # Returns 42
    """

    _value: T

    def __init__(self, value: T) -> None:
        """Initialize literal with value.

        Args:
            value: The native Python value to wrap
        """
        self._value = value

    def execute(self, context: ContextT) -> T:
        """Execute returns the wrapped value.

        Args:
            context: Unused for literals

        Returns:
            The wrapped value
        """
        return self._value

    def unwrap(self) -> T:
        """Get the wrapped value directly.

        Returns:
            The wrapped value
        """
        return self._value

    def __repr__(self) -> str:
        """Machine-readable representation."""
        return f"{self.__class__.__name__}({self._value!r})"

    def __str__(self) -> str:
        """Human-readable representation."""
        return str(self._value)
