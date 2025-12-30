"""Convert python objects to Literal and Computed values."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..term import ComputedValue, RValue

__all__ = [
    "computed",
    "literal",
]


def literal(value: object) -> RValue:
    """Wrap value in LiteralValue if not already an RValue.

    Helper for operator overloading - converts Python literals
    to RValue terms automatically.

    Args:
        value: Value to wrap (can be RValue or literal)

    Returns:
        LiteralValue (unchanged if already RValue, wrapped otherwise)

    Example:
        >>> literal(42)  # → IntLiteral(42)
        >>> literal(price.get())  # → price.get() (unchanged)
    """
    from ..term import RValue
    from .literals import (
        BoolLiteral,
        BytesLiteral,
        DictLiteral,
        FloatLiteral,
        FrozenSetLiteral,
        IntLiteral,
        ListLiteral,
        NoneLiteral,
        SetLiteral,
        StrLiteral,
        TupleLiteral,
    )

    if isinstance(value, RValue):
        return value
    elif isinstance(value, bool):  # Must check bool before int (bool is subclass of int)
        return BoolLiteral(value)
    elif isinstance(value, int):
        return IntLiteral(value)
    elif isinstance(value, str):
        return StrLiteral(value)
    elif isinstance(value, float):
        return FloatLiteral(value)
    elif isinstance(value, bytes):
        return BytesLiteral(value)
    elif value is None:
        return NoneLiteral()
    elif isinstance(value, dict):
        return DictLiteral(value)
    elif isinstance(value, set):
        return SetLiteral(value)
    elif isinstance(value, list):
        return ListLiteral(value)
    elif isinstance(value, tuple):
        return TupleLiteral(value)
    elif isinstance(value, frozenset):
        return FrozenSetLiteral(value)
    else:
        raise TypeError(f"Not supported type {value.__class__.__name__}")


def computed(result_type: object, op: RValue) -> ComputedValue:
    """Return wrapped computed value for an op.

    Args:
        result_type: Expected result type
        op: Operation to wrap

    Returns:
        Typed computed value wrapper
    """
    from .values import (
        BoolValue,
        BytesValue,
        DictValue,
        FloatValue,
        FrozenSetValue,
        IntValue,
        ListValue,
        NoneValue,
        SetValue,
        StrValue,
        TupleValue,
    )

    if result_type is int:
        return IntValue(op)
    elif result_type is str:
        return StrValue(op)
    elif result_type is bool:
        return BoolValue(op)
    elif result_type is float:
        return FloatValue(op)
    elif result_type is bytes:
        return BytesValue(op)
    elif result_type is None:
        return NoneValue(op)
    elif result_type is dict:
        return DictValue(op)
    elif result_type is set:
        return SetValue(op)
    elif result_type is list:
        return ListValue(op)
    elif result_type is tuple:
        return TupleValue(op)
    elif result_type is frozenset:
        return FrozenSetValue(op)
    else:
        raise TypeError(f"Unknown type `{result_type.__class__.__name__}`")
