"""Logical capability bases.

Atomic:
    AndableBase: and_()
    OrableBase: or_()
    NotableBase: not_(), bool_()

Combined:
    LogicalBase = Andable + Orable + Notable
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from everyabc import Term


__all__ = [
    "AndableBase",
    "LogicalBase",
    "NotableBase",
    "OrableBase",
]


class AndableBase[OperandT, ResultT]:
    """Base for values that support logical AND."""

    def _wrap_logical_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def and_(self, other: OperandT) -> ResultT:
        """Logical AND: self AND other."""
        from everybase.morphisms import AndOp

        return cast("ResultT", self._wrap_logical_result(AndOp(self, other)))


class OrableBase[OperandT, ResultT]:
    """Base for values that support logical OR."""

    def _wrap_logical_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def or_(self, other: OperandT) -> ResultT:
        """Logical OR: self OR other."""
        from everybase.morphisms import OrOp

        return cast("ResultT", self._wrap_logical_result(OrOp(self, other)))


class NotableBase[ResultT]:
    """Base for values that support logical NOT and bool conversion."""

    def _wrap_logical_result(self, operand: Term) -> Term:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def __bool__(self) -> bool:
        """Bool conversion is blocked in DSL context.

        Raises:
            TypeError: Cannot convert to bool directly
        """
        raise TypeError(
            "Cannot convert Term to bool directly. Use .bool_() method or explicit comparisons."
        )

    def __and__(self, other: object) -> object:
        """Bitwise AND is blocked; use and_() method."""
        raise TypeError("Cannot use & operator on Terms. Use .and_(other) method instead.")

    def __or__(self, other: object) -> object:
        """Bitwise OR is blocked; use or_() method."""
        raise TypeError("Cannot use | operator on Terms. Use .or_(other) method instead.")

    def not_(self) -> ResultT:
        """Logical NOT: NOT self."""
        from everybase.morphisms import NotOp

        return cast("ResultT", self._wrap_logical_result(NotOp(self)))

    def bool_(self) -> ResultT:
        """Convert to boolean value."""
        from everybase.morphisms import BoolOp

        return cast("ResultT", self._wrap_logical_result(BoolOp(self)))


class LogicalBase[OperandT, ResultT](
    AndableBase[OperandT, ResultT],
    OrableBase[OperandT, ResultT],
    NotableBase[ResultT],
):
    """Full logical: and_(), or_(), not_(), bool_()."""

    pass
