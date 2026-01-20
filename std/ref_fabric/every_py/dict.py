"""Dictionary type for Term expressions.

This module provides DictType which represents dict expressions (literal or computed).
Supports key access, keys/values/items operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from .bases import BaseType, ComparisonBase, MappingBase


if TYPE_CHECKING:
    from every._abc import Term

    from .any import AnyType
    from .bool import BoolType
    from .list import ListType


__all__ = [
    "DictType",
]


class DictType[K, V](
    MappingBase[K, V, "DictType[K, V]"],
    ComparisonBase[dict[K, V]],
    BaseType[dict[K, V]],
):
    """Dict type - represents dict expressions (literal or computed).

    Supports key access, keys/values/items operations.

    Example:
        >>> x = DictType({"a": 1, "b": 2})
        >>> y = x["a"]  # Returns AnyType
        >>> z = x.keys_()  # Returns ListType[K]
    """

    VALUE_TYPE: ClassVar[type] = dict

    def _wrap_comparison_result(self, operand: Term) -> BoolType:
        from .bool import BoolType

        return BoolType(operand)

    def _wrap_keys_result(self, operand: Term) -> ListType:
        from .list import ListType

        return ListType(operand)

    def _wrap_values_result(self, operand: Term) -> ListType:
        from .list import ListType

        return ListType(operand)

    def _wrap_items_result(self, operand: Term) -> ListType:
        from .list import ListType

        return ListType(operand)

    def _wrap_value_result(self, operand: Term) -> AnyType:
        from .any import AnyType

        return AnyType(operand)

    def __getitem__(self, key: K) -> AnyType:
        from term.ops import AtOp

        from .any import AnyType

        return AnyType(AtOp(self, key))
