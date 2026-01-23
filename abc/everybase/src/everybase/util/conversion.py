"""Convert Python objects to Ref expressions.

This module provides conversion utilities for the unified Ref system:
- ensure_term(): Wrap Python values in appropriate Ref classes
- typed_ref(): Wrap operations in typed Ref classes
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from every import Ref, Term

__all__ = [
    "ensure_term",
    "typed_ref",
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
        >>> ensure_term(42)  # → IntRef(42)
        >>> ensure_term("hello")  # → StrRef("hello")
        >>> ensure_term(price.get())  # → price.get() (unchanged)
    """
    from every import Term
    from everybase.py import (
        BoolRef,
        BytesRef,
        DictRef,
        FloatRef,
        FrozenSetRef,
        IntRef,
        ListRef,
        NoneRef,
        SetRef,
        StrRef,
        TupleRef,
    )

    if isinstance(value, Term):
        return value
    elif isinstance(value, bool):  # Must check bool before int (bool is subclass)
        return BoolRef(value)
    elif isinstance(value, int):
        return IntRef(value)
    elif isinstance(value, str):
        return StrRef(value)
    elif isinstance(value, float):
        return FloatRef(value)
    elif isinstance(value, bytes):
        return BytesRef(value)
    elif value is None:
        return NoneRef()
    elif isinstance(value, dict):
        return DictRef(value)
    elif isinstance(value, set):
        return SetRef(value)
    elif isinstance(value, list):
        return ListRef(value)
    elif isinstance(value, tuple):
        return TupleRef(value)
    elif isinstance(value, frozenset):
        return FrozenSetRef(value)
    else:
        logger.error(f"Not supported type {value.__class__.__name__}")
        raise TypeError(f"Not supported type {value.__class__.__name__}")


def typed_ref(result_type: object, op: Term) -> Ref:
    """Wrap an operation in a typed Ref.

    Args:
        result_type: Expected result type (e.g., int, str, float)
        op: Operation to wrap

    Returns:
        Typed Ref wrapping the operation

    Example:
        >>> typed_ref(int, GetOp(ref))  # → IntRef(GetOp(ref))
        >>> typed_ref(str, some_op)  # → StrRef(some_op)
    """
    from everybase.py import (
        AnyRef,
        BoolRef,
        BytesRef,
        DictRef,
        FloatRef,
        FrozenSetRef,
        IntRef,
        ListRef,
        NoneRef,
        SetRef,
        StrRef,
        TupleRef,
    )

    if result_type is int:
        return IntRef(op)
    elif result_type is str:
        return StrRef(op)
    elif result_type is bool:
        return BoolRef(op)
    elif result_type is float:
        return FloatRef(op)
    elif result_type is bytes:
        return BytesRef(op)
    elif result_type is None:
        return NoneRef(None)
    elif result_type is dict:
        return DictRef(op)
    elif result_type is set:
        return SetRef(op)
    elif result_type is list:
        return ListRef(op)
    elif result_type is tuple:
        return TupleRef(op)
    elif result_type is frozenset:
        return FrozenSetRef(op)
    else:
        logger.debug(f"Unknown type `{result_type}` for term `{op}`")
        return AnyRef(op)
