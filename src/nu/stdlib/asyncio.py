"""Asyncio-backed Commands. ASYNC-mode wrappers over asyncio primitives."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from nu.terms import Mode, UnaryAtomic


if TYPE_CHECKING:
    from nu.terms import FloatArg


__all__ = ["AsyncSleep"]


class AsyncSleep(UnaryAtomic):
    """Yield to the event loop for ``delay`` seconds. Wraps `asyncio.sleep`.

    Children: ``[delay]``
    """

    mode: ClassVar[Mode] = Mode.ASYNC

    def __init__(self, delay: FloatArg) -> None:
        super().__init__(delay)

    async def apply(self, delay: float) -> None:
        await asyncio.sleep(delay)
