from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .binary_ops import BinaryOp


class ErgonomicsMixin[T]:
    def __add__(self, other: object) -> BinaryOp[T]:
        """Addition: self + other.

        Creates BinaryOp("add", self, other).
        Converts literals to LiteralValue automatically.

        Args:
            other: Right operand (RValue or literal)

        Returns:
            BinaryOp operation

        Example:
            >>> price = item.price.get()
            >>> total = price + 10  # price.__add__(10)
        """
        from ..term import RValue
        from .binary_ops import BinaryOp
        from .literal_value import LiteralValue

        right = other if isinstance(other, RValue) else LiteralValue(other)
        return BinaryOp("add", self, right)

    def __radd__(self, other: object) -> BinaryOp[T]:
        """Right addition: other + self.

        Called when left operand doesn't support __add__.

        Args:
            other: Left operand (LiteralValue)

        Returns:
            BinaryOp operation

        Example:
            >>> price = item.price.get()
            >>> total = 10 + price  # price.__radd__(10)
        """
        from .binary_ops import BinaryOp
        from .literal_value import LiteralValue

        left = LiteralValue(other)
        return BinaryOp("add", left, self)
