"""Concrete none value for Python memory storage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import NoneType
from ..base import ValueBase


if TYPE_CHECKING:
    from everybase.core import Arg, Context, Sentinel


class NoneValue(ValueBase[None], NoneType):
    """Concrete none value for Python memory storage."""

    def __init__(self, source: Arg[None] = None) -> None:
        """Initialize with None as default source."""
        super().__init__(source)

    async def fetch(self, ctx: Context) -> None | Sentinel:
        """Get returns None."""
        return None
