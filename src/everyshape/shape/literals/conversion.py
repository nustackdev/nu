"""Convert python objects to Literal values."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..term import RValue


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
    from ..term import RValue
    from .primitive_values import BoolValue, BytesValue, FloatValue, IntValue, NoneValue, StrValue

    if isinstance(value, RValue):
        return value
    elif isinstance(value, int):
        return IntValue(value)
    elif isinstance(value, str):
        return StrValue(value)
    elif isinstance(value, bool):
        return BoolValue(value)
    elif isinstance(value, float):
        return FloatValue(value)
    elif isinstance(value, bytes):
        return BytesValue(value)
    elif value is None:
        return NoneValue()
    else:
        raise TypeError(f"Not supported type {value.__class__.__name__}")
