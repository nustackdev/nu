"""Set types for Term expressions.

This module provides SetType and FrozenSetType which represent set expressions
(literal or computed). Supports containment testing, length, and set operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from .base_collections import SetBase
from .base_comparison import ComparisonBase
from .type import Type


if TYPE_CHECKING:
    from ..term import Term
    from .bool_type import BoolType


__all__ = [
    "FrozenSetType",
    "SetType",
]


class SetType[T](
    SetBase[T, "SetType[T]"],
    ComparisonBase[set[T]],
    Type[set[T]],
):
    """Set type - represents set expressions (literal or computed).

    Supports containment testing, length, and set operations.

    Example:
        >>> x = SetType({1, 2, 3})
        >>> y = x.contains(2)  # Returns BoolType
        >>> z = x.union({4})  # Returns SetType
    """

    VALUE_TYPE: ClassVar[type] = set

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        from .bool_type import BoolType

        return BoolType(operand)

    def _wrap_set_result(self, operand: Term) -> SetType[T]:
        return SetType(operand)


class FrozenSetType[T](
    SetBase[T, "FrozenSetType[T]"],
    ComparisonBase[frozenset[T]],
    Type[frozenset[T]],
):
    """FrozenSet type - represents frozenset expressions (literal or computed).

    Immutable version of SetType.

    Example:
        >>> x = FrozenSetType(frozenset({1, 2, 3}))
        >>> y = x.contains(2)  # Returns BoolType
    """

    VALUE_TYPE: ClassVar[type] = frozenset

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        from .bool_type import BoolType

        return BoolType(operand)

    def _wrap_set_result(self, operand: Term) -> FrozenSetType[T]:
        return FrozenSetType(operand)
