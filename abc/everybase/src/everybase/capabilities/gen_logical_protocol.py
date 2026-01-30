# ruff: noqa: D102
"""Logical capability protocols.

Atomic:
    AndableProtocol: and_()
    OrableProtocol: or_()
    NotableProtocol: not_(), bool_()

Combined:
    LogicalProtocol = Andable + Orable + Notable
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


__all__ = [
    "AndableProtocol",
    "LogicalProtocol",
    "NotableProtocol",
    "OrableProtocol",
]


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
