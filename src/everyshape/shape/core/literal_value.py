"""Literal value term implementation.

Used to represent constant values in the term graph.
This is similar to Python's own literal values, but wrapped in a term
to participate in the EveryShape computation model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..term import Operation, RValue


if TYPE_CHECKING:
    from ..context import Context


class LiteralValue[T](Operation[T]):
    """Constant literal value.

    Represents compile-time constants: numbers, strings, booleans, etc.
    Always pure, always returns the same value.

    Example:
        >>> LiteralValue(42).execute(ctx)
        42
        >>> LiteralValue("hello").execute(ctx)
        "hello"
    """

    def __init__(self, value: T) -> None:
        """Initialize literal.

        Args:
            value: The constant value
        """
        self.value = value
        self.children = ()

    def execute(self, context: Context) -> T:
        """Return the constant value.

        Args:
            context: Unused

        Returns:
            The constant value
        """
        return self.value

    def __repr__(self) -> str:
        """String representation."""
        return f"LiteralValue({self.value!r})"


def literal(value: object) -> RValue:
    """Wrap value in LiteralValue if not already an RValue.

    Helper for operator overloading - converts Python literals
    to RValue terms automatically.

    Args:
        value: Value to wrap (can be RValue or literal)

    Returns:
        RValue (unchanged if already RValue, wrapped otherwise)

    Example:
        >>> literal(42)  # → LiteralValue(42)
        >>> literal(price.get())  # → price.get() (unchanged)
    """
    if isinstance(value, RValue):
        return value
    return LiteralValue(value)
