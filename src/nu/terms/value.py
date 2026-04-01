"""Typed value holder.

Nu                          - the primitive
└── RValue                  - evaluable expression
    └── Value               - literal or computed data (leaf Nu)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .nu import RValue
from .type_vars import T_co


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Value",
]


class Value(RValue[T_co], ABC):
    """Typed value holder - literal or computed.

    Values are leaf Nus that hold data directly or wrap a source Nu.
    They have no address and cannot be written to.

    Substrate-specific bases (ValueBase, etc.) implement execute().
    """

    @abstractmethod
    async def execute(self, ctx: Context) -> T_co:
        ...

    @property
    def is_self_pure(self) -> bool:
        """Values never have side effects."""
        return True
