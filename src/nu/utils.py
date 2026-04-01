"""Convert Python objects to Nu expressions.

Provides:
- ensure_nu(): Wrap Python values in appropriate Interface classes
- typed_value(): Wrap operations in typed Interface classes
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.terms import Nu, Value

__all__ = [
    "ensure_nu",
    "typed_value",
]

logger = logging.getLogger(__name__)


def ensure_nu(value: object) -> Nu:
    """Ensure value is a Nu, wrapping in appropriate Interface if needed.

    Converts Python literals to Interface expressions automatically.
    If already a Nu, returns unchanged.

    Args:
        value: Value to ensure is a Nu (can be Nu or literal)

    Returns:
        Nu (unchanged if already Nu, wrapped in Interface otherwise)

    Example:
        >>> ensure_nu(42)  # → IntI(42)
        >>> ensure_nu("hello")  # → StrI("hello")
        >>> ensure_nu(price.get())  # → price.get() (unchanged)
    """
    from nu.terms import Nu

    from nu.interfaces.primitives import BoolI, BytesI, FloatI, IntI, NoneI, StrI
    from nu.interfaces.collections import DictI, FrozenSetI, ListI, SetI, TupleI

    if isinstance(value, Nu):
        return value
    elif isinstance(value, bool):  # Must check bool before int (bool is subclass)
        return BoolI(value)
    elif isinstance(value, int):
        return IntI(value)
    elif isinstance(value, str):
        return StrI(value)
    elif isinstance(value, float):
        return FloatI(value)
    elif isinstance(value, bytes):
        return BytesI(value)
    elif value is None:
        return NoneI()
    elif isinstance(value, dict):
        return DictI(value)
    elif isinstance(value, set):
        return SetI(value)
    elif isinstance(value, list):
        return ListI(value)
    elif isinstance(value, tuple):
        return TupleI(value)
    elif isinstance(value, frozenset):
        return FrozenSetI(value)
    else:
        logger.error(f"Not supported type {value.__class__.__name__}")
        raise TypeError(f"Not supported type {value.__class__.__name__}")


def typed_value(result_type: object, op: Nu) -> Nu:
    """Wrap an operation in a typed Interface.

    Args:
        result_type: Expected result type (e.g., int, str, float)
        op: Nu to wrap

    Returns:
        Typed Interface wrapping the operation

    Example:
        >>> typed_value(int, GetOp(ref))  # → IntI(GetOp(ref))
        >>> typed_value(str, some_op)  # → StrI(some_op)
    """
    from nu.interfaces.primitives import BoolI, BytesI, FloatI, IntI, NoneI, StrI
    from nu.interfaces.collections import DictI, FrozenSetI, ListI, SetI, TupleI
    from nu.interfaces.special import AnyI

    if result_type is int:
        return IntI(op)
    elif result_type is str:
        return StrI(op)
    elif result_type is bool:
        return BoolI(op)
    elif result_type is float:
        return FloatI(op)
    elif result_type is bytes:
        return BytesI(op)
    elif result_type is None:
        return NoneI()
    elif result_type is dict:
        return DictI(op)
    elif result_type is set:
        return SetI(op)
    elif result_type is list:
        return ListI(op)
    elif result_type is tuple:
        return TupleI(op)
    elif result_type is frozenset:
        return FrozenSetI(op)
    else:
        logger.debug(f"Unknown type `{result_type}` for Nu `{op}`")
        return AnyI(op)
