"""Asyncio-backed Flows. ASYNC-only wrappers over asyncio primitives.

`AsyncSleep` is a Control: takes a delay Query parameter, no body slots.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import FloatArg


__all__ = ["AsyncSleep"]


class AsyncSleep(Control):
    """Yield to the event loop for ``delay`` seconds. Wraps `asyncio.sleep`.

    Children: ``[delay]`` (Query parameter, no body slots).
    """

    body_slots: ClassVar[tuple[int, ...] | None] = None
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, delay: FloatArg) -> None:
        super().__init__(delay)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        delay = await self._children[0].aeval(ctx)
        await asyncio.sleep(delay)
