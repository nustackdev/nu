"""Convert Python objects to Type expressions.

This module provides conversion utilities for the unified Type system:
- literal(): Wrap Python values in appropriate Type classes
- computed(): Wrap operations in typed Type classes
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from every import Term, Type

__all__ = [
    "computed",
    "literal",
]

logger = logging.getLogger(__name__)


def literal(value: object) -> Term:
    """Wrap value in appropriate Type if not already an Term.

    Helper for operator overloading - converts Python literals
    to Type expressions automatically.

    Args:
        value: Value to wrap (can be Term or literal)

    Returns:
        Type expression (unchanged if already Term, wrapped otherwise)

    Example:
        >>> literal(42)  # → IntType(42)
        >>> literal("hello")  # → StrType("hello")
        >>> literal(price.get())  # → price.get() (unchanged)
    """
    from every import Term
    from everybase.types import (
        BoolType,
        BytesType,
        DictType,
        FloatType,
        FrozenSetType,
        IntType,
        ListType,
        NoneType,
        SetType,
        StrType,
        TupleType,
    )

    if isinstance(value, Term):
        return value
    elif isinstance(value, bool):  # Must check bool before int (bool is subclass)
        return BoolType(value)
    elif isinstance(value, int):
        return IntType(value)
    elif isinstance(value, str):
        return StrType(value)
    elif isinstance(value, float):
        return FloatType(value)
    elif isinstance(value, bytes):
        return BytesType(value)
    elif value is None:
        return NoneType()
    elif isinstance(value, dict):
        return DictType(value)
    elif isinstance(value, set):
        return SetType(value)
    elif isinstance(value, list):
        return ListType(value)
    elif isinstance(value, tuple):
        return TupleType(value)
    elif isinstance(value, frozenset):
        return FrozenSetType(value)
    else:
        logger.error(f"Not supported type {value.__class__.__name__}")
        raise TypeError(f"Not supported type {value.__class__.__name__}")


def computed(result_type: object, op: Term) -> Type:
    """Return wrapped Type for an operation.

    Args:
        result_type: Expected result type (e.g., int, str, float)
        op: Operation to wrap

    Returns:
        Typed Type wrapper

    Example:
        >>> computed(int, GetOp(ref))  # → IntType(GetOp(ref))
        >>> computed(str, some_op)  # → StrType(some_op)
    """
    from everybase.types import (
        AnyType,
        BoolType,
        BytesType,
        DictType,
        FloatType,
        FrozenSetType,
        IntType,
        ListType,
        NoneType,
        SetType,
        StrType,
        TupleType,
    )

    if result_type is int:
        return IntType(op)
    elif result_type is str:
        return StrType(op)
    elif result_type is bool:
        return BoolType(op)
    elif result_type is float:
        return FloatType(op)
    elif result_type is bytes:
        return BytesType(op)
    elif result_type is None:
        return NoneType(None)
    elif result_type is dict:
        return DictType(op)
    elif result_type is set:
        return SetType(op)
    elif result_type is list:
        return ListType(op)
    elif result_type is tuple:
        return TupleType(op)
    elif result_type is frozenset:
        return FrozenSetType(op)
    else:
        logger.debug(f"Unknown type `{result_type}` for term `{op}`")
        return AnyType(op)
