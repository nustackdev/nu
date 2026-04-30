"""Timing policies - Timeout, Throttle, Debounce.

Span:Policy kinds that wrap a body Command with timing-related rules.
ASYNC-only (rely on the asyncio loop for cancellation / scheduling).

For wall-clock measurement see `nu.queries.timing.Timed`.
For sleep primitives see `nu.stdlib.asyncio.AsyncSleep`.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.span import Policy
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import FloatArg, Nu


__all__ = [
    "Debounce",
    "Throttle",
    "Timeout",
]


_ASYNC = frozenset({Mode.ASYNC})


async def _resolve(ctx: Any, val: Any) -> Any:  # noqa: ANN401
    from nu import runtime
    from nu.terms.nu import NuBase

    if isinstance(val, NuBase):
        return await runtime.afirst(val, ctx)
    return val


class Timeout(Policy):
    """Run body with a wall-clock time limit.

    Children: `[body]`. `timeout` and `on_timeout` kept on the instance
    so the body slot semantics stay clean (body_slot = 0).
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = _ASYNC

    def __init__(
        self,
        timeout: FloatArg,
        body: Nu,
        on_timeout: Nu | None = None,
    ) -> None:
        super().__init__(body)
        self._timeout = timeout
        self._on_timeout = on_timeout

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        from nu import runtime

        timeout = float(await _resolve(ctx, self._timeout))
        try:
            return await asyncio.wait_for(call(), timeout=timeout)
        except TimeoutError:
            if self._on_timeout is not None:
                await runtime.aexecute(self._on_timeout, ctx)
                return None
            raise


class Throttle(Policy):
    """Drop body executions inside `interval` seconds of the prior run.

    Children: `[body]`. `interval` kept on the instance.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = _ASYNC

    def __init__(self, interval: FloatArg, body: Nu) -> None:
        super().__init__(body)
        self._interval = interval
        self._last_time: float = 0.0

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        interval = float(await _resolve(ctx, self._interval))
        now = time.monotonic()
        if now - self._last_time < interval:
            return None
        self._last_time = now
        return await call()


class Debounce(Policy):
    """Delay body execution by `delay`; cancel pending on re-entry.

    Children: `[body]`. Each invocation cancels any in-flight task and
    starts a fresh timer.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = _ASYNC

    def __init__(self, delay: FloatArg, body: Nu) -> None:
        super().__init__(body)
        self._delay = delay
        self._pending: asyncio.Task | None = None

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        delay = float(await _resolve(ctx, self._delay))
        if self._pending is not None and not self._pending.done():
            self._pending.cancel()

        async def _later() -> Any:
            await asyncio.sleep(delay)
            return await call()

        self._pending = asyncio.create_task(_later())
        return None
