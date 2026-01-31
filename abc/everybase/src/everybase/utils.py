"""Convert Python objects to Ref expressions.

This module provides conversion utilities for the unified Ref system:
- ensure_term(): Wrap Python values in appropriate Ref classes
- typed_value(): Wrap operations in typed Ref classes
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyabc import Term, Value

__all__ = [
    "ensure_term",
    "typed_value",
]

logger = logging.getLogger(__name__)


def ensure_term(value: object) -> Term:
    """Ensure value is a Term, wrapping in appropriate Ref if needed.

    Converts Python literals to Ref expressions automatically.
    If already a Term, returns unchanged.

    Args:
        value: Value to ensure is a Term (can be Term or literal)

    Returns:
        Term (unchanged if already Term, wrapped in Ref otherwise)

    Example:
        >>> ensure_term(42)  # → IntValue(42)
        >>> ensure_term("hello")  # → StrValue("hello")
        >>> ensure_term(price.get())  # → price.get() (unchanged)
    """
    from everyabc import Term
    from everybase.values import (
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

    if isinstance(value, Term):
        return value
    elif isinstance(value, bool):  # Must check bool before int (bool is subclass)
        return BoolValue(value)
    elif isinstance(value, int):
        return IntValue(value)
    elif isinstance(value, str):
        return StrValue(value)
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
        logger.error(f"Not supported type {value.__class__.__name__}")
        raise TypeError(f"Not supported type {value.__class__.__name__}")


def typed_value(result_type: object, op: Term) -> Value:
    """Wrap an operation in a typed Value.

    Args:
        result_type: Expected result type (e.g., int, str, float)
        op: Operation to wrap

    Returns:
        Typed Value wrapping the operation

    Example:
        >>> typed_value(int, GetOp(ref))  # → IntValue(GetOp(ref))
        >>> typed_value(str, some_op)  # → StrValue(some_op)
    """
    from everybase.values import (
        AnyValue,
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
        return NoneValue()
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
        logger.debug(f"Unknown type `{result_type}` for term `{op}`")
        return AnyValue(op)
