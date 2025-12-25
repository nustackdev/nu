"""Convert python objects to Literal values."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..term import RValue
    from .base import Literal

__all__ = [
    "literal",
    "result",
]


def literal(value: object) -> Literal:
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
    from .collection_values import DictValue, FrozenSetValue, ListValue, SetValue, TupleValue
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
    elif isinstance(value, dict):
        return DictValue(value)
    elif isinstance(value, set):
        return SetValue(value)
    elif isinstance(value, list):
        return ListValue(value)
    elif isinstance(value, tuple):
        return TupleValue(value)
    elif isinstance(value, frozenset):
        return FrozenSetValue(value)
    else:
        raise TypeError(f"Not supported type {value.__class__.__name__}")


def result(reslut_type: object, op: RValue) -> Literal:
    """Return wrapped compted value for an op."""
    from .collection_values import DictValue, FrozenSetValue, ListValue, SetValue, TupleValue
    from .primitive_values import BoolValue, BytesValue, FloatValue, IntValue, NoneValue, StrValue

    if reslut_type is int:
        return IntValue(op)
    elif reslut_type is str:
        return StrValue(op)
    elif reslut_type is bool:
        return BoolValue(op)
    elif reslut_type is float:
        return FloatValue(op)
    elif reslut_type is bytes:
        return BytesValue(op)
    elif reslut_type is None:
        return NoneValue(op)
    elif reslut_type is dict:
        return DictValue(op)
    elif reslut_type is set:
        return SetValue(op)
    elif reslut_type is list:
        return ListValue(op)
    elif reslut_type is tuple:
        return TupleValue(op)
    elif reslut_type is frozenset:
        return FrozenSetValue(op)
    else:
        raise TypeError(f"Unknown type {type(op).__name__}")
