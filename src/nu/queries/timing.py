"""Timing scalars - Timed.

`Timed` runs a body and returns its elapsed duration as a float.

For sleep primitives see `nu.stdlib.asyncio.AsyncSleep` and
`nu.stdlib.time.TimeSleep`. For timeout / throttle / debounce policies
see `nu.spans.timing`.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import Nu


__all__ = ["Timed"]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Timed(ScalarQuery):
    """Run a body and return wall-clock duration in seconds.

    Children: `[body]`.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, body: Nu, *, label: str = "Timed") -> None:
        super().__init__(body)
        self._label = label

    def eval(self, ctx: Any) -> float:  # noqa: ANN401
        from nu import runtime

        t0 = time.perf_counter()
        runtime.execute(self._children[0], ctx)
        return time.perf_counter() - t0

    async def aeval(self, ctx: Any) -> float:  # noqa: ANN401
        from nu import runtime

        t0 = time.perf_counter()
        await runtime.aexecute(self._children[0], ctx)
        return time.perf_counter() - t0
