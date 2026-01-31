"""Typed value holder (RValue).

Term                        - executable node
└── RValue                  - evaluable expression
    └── Value               - typed value holder

Value is the base for typed values — literal data or computed results.
Substrate bases (ValueBase, etc.) implement execute().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .term import RValue
from .type_vars import T_co


if TYPE_CHECKING:
    from everyabc.context import Context


__all__ = [
    "Value",
]


class Value(RValue[T_co], ABC):
    """Typed value holder — literal or computed.

    Values are RValues that hold data directly or wrap a source Term.
    They have no address and cannot be written to.

    Substrate-specific bases (ValueBase, etc.) implement execute().
    """

    @abstractmethod
    async def execute(self, ctx: Context) -> T_co:
        """Execute this value within a context.

        Args:
            ctx: Execution context.

        Returns:
            The value.
        """
        ...

    @property
    def is_self_pure(self) -> bool:
        """Values never have side effects."""
        return True
