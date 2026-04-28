"""Time-backed Flows. SYNC-mode wrappers over the ``time`` module.

`TimeSleep` is a Control: takes a delay Query parameter, no body slots.
It runs the wall-clock side effect after evaluating the delay.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Control
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import FloatArg


__all__ = ["TimeSleep"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class TimeSleep(Control):
    """Block the thread for ``delay`` seconds. Wraps `time.sleep`.

    Children: ``[delay]`` (Query parameter, no body slots).
    """

    body_slots: ClassVar[tuple[int, ...] | None] = None
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, delay: FloatArg) -> None:
        super().__init__(delay)

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        delay = self._children[0].eval(ctx)
        time.sleep(delay)

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        delay = await self._children[0].aeval(ctx)
        time.sleep(delay)
