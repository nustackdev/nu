# ruff: noqa: D102
"""Logical capabilities — protocols + bases.

Atomic:
    AndableProtocol/Base: and_()
    OrableProtocol/Base: or_()
    NotableProtocol/Base: not_(), bool_()

Combined:
    LogicalProtocol/Base = Andable + Orable + Notable
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = [
    "AndableBase",
    "AndableProtocol",
    "LogicalBase",
    "LogicalProtocol",
    "NotableBase",
    "NotableProtocol",
    "OrableBase",
    "OrableProtocol",
]


# =============================================================================
# PROTOCOLS
# =============================================================================


@runtime_checkable
class AndableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support logical AND."""

    def and_(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class OrableProtocol[OperandT, ResultT](Protocol):
    """Protocol for values that support logical OR."""

    def or_(self, other: OperandT) -> ResultT: ...


@runtime_checkable
class NotableProtocol[ResultT](Protocol):
    """Protocol for values that support logical NOT and bool conversion."""

    def not_(self) -> ResultT: ...
    def bool_(self) -> ResultT: ...


class LogicalProtocol[OperandT, ResultT](
    AndableProtocol[OperandT, ResultT],
    OrableProtocol[OperandT, ResultT],
    NotableProtocol[ResultT],
    Protocol,
):
    """Full logical protocol."""

    ...


# =============================================================================
# BASES
# =============================================================================


class AndableBase[OperandT, ResultT]:
    """Base for values that support logical AND."""

    def _wrap_logical_result(self, operand: Nu) -> Nu:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def and_(self, other: OperandT) -> ResultT:
        """Logical AND: self AND other."""
        from nu.ops import AndOp

        return cast("ResultT", self._wrap_logical_result(AndOp(self, other)))


class OrableBase[OperandT, ResultT]:
    """Base for values that support logical OR."""

    def _wrap_logical_result(self, operand: Nu) -> Nu:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def or_(self, other: OperandT) -> ResultT:
        """Logical OR: self OR other."""
        from nu.ops import OrOp

        return cast("ResultT", self._wrap_logical_result(OrOp(self, other)))


class NotableBase[ResultT]:
    """Base for values that support logical NOT and bool conversion.

    Python ``bool()`` / ``if node:`` use default truthiness (always True,
    inherited from ``Nu.__bool__``).
    Use ``.bool_()`` for DSL-level bool that builds expression trees.
    """

    def _wrap_logical_result(self, operand: Nu) -> Nu:
        """Override in subclass to wrap result in appropriate type."""
        raise NotImplementedError()

    def not_(self) -> ResultT:
        """Logical NOT: NOT self."""
        from nu.ops import NotOp

        return cast("ResultT", self._wrap_logical_result(NotOp(self)))

    def bool_(self) -> ResultT:
        """Convert to boolean value."""
        from nu.ops import BoolOp

        return cast("ResultT", self._wrap_logical_result(BoolOp(self)))


class LogicalBase[OperandT, ResultT](
    AndableBase[OperandT, ResultT],
    OrableBase[OperandT, ResultT],
    NotableBase[ResultT],
):
    """Full logical: and_(), or_(), not_(), bool_()."""

    pass
