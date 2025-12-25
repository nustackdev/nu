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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..term import Operation, RValue


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Computed",
    "Literal",
    "ValueBase",
]


class ValueBase[T](Operation[T], ABC):
    """Base class for value types (literal value - LiteralValue and computable values).

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

    def __init__(self, value: T) -> None:
        """Initialize literal with value.

        Args:
            value: The native Python value to wrap
        """
        self._value = value

    @abstractmethod
    def execute(self, context: Context) -> T:
        """Execute returns the wrapped value.

        Args:
            context: Unused for literals

        Returns:
            The wrapped value
        """
        ...

    def __repr__(self) -> str:
        """Machine-readable representation."""
        return f"{self.__class__.__name__}({self._value!r})"

    def __str__(self) -> str:
        """Human-readable representation."""
        return str(self._value)


class Computed[T: RValue](ValueBase[T]):
    """Base class for literal (constant) RValues.

    Literal values wrap native Python values directly and don't
    require any computation to produce their value.

    Type Parameters:
        T: The native Python type this literal wraps
        ContextT: The execution context type

    Example:
        >>> lit = IntComputed(ref)
        >>> lit.execute(ctx)  # Returns 42
    """

    def execute(self, context: Context) -> T:
        """Execute returns the wrapped value.

        Args:
            context: Unused for literals

        Returns:
            The wrapped value
        """
        return self._value.execute(context)


class Literal[T](ValueBase[T], ABC):
    """Base class for literal (constant) RValues.

    Literal values wrap native Python values directly and don't
    require any computation to produce their value.

    Type Parameters:
        T: The native Python type this literal wraps
        ContextT: The execution context type

    Example:
        >>> lit = IntLiteral(42)
        >>> lit.execute(ctx)  # Returns 42
    """

    def execute(self, context: Context) -> T:
        """Execute returns the wrapped value.

        Args:
            context: Unused for literals

        Returns:
            The wrapped value
        """
        if isinstance(self._value, RValue):
            return self._value.execute(context)
        return self._value
