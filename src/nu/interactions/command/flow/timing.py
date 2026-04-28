"""Timing ops -- Timed, Timeout, Throttle, Debounce.

For sleep primitives, see ``nu.stdlib.asyncio.AsyncSleep`` (ASYNC) and
``nu.stdlib.time.TimeSleep`` (SYNC). Core ships no ``Delay``: asyncio.sleep
and time.sleep live in stdlib.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.span import Policy
from nu.terms.types import Mode


if TYPE_CHECKING:
    from nu.terms import FloatArg, Nu


__all__ = [
    "Debounce",
    "Throttle",
    "Timed",
    "Timeout",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})


class Timed(ScalarQuery):
    """Run a body and return its elapsed duration in seconds.

    Children: ``[body]``. ``support`` covers sync and async; the body
    runs via ``runtime.execute`` / ``runtime.aexecute`` and the wall-clock
    delta is returned as a float.
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


class Timeout(Policy):
    """Run body with a wall-clock time limit.

    Children: ``[body]``. ``timeout`` and ``on_timeout`` kept on the
    instance so the body slot semantics stay clean (body_slot = 0).
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(
        self,
        timeout: FloatArg,
        body: Nu,
        on_timeout: Nu | None = None,
    ) -> None:
        super().__init__(body)
        self._timeout = timeout
        self._on_timeout = on_timeout

    async def _resolve(self, ctx: Any, val: Any) -> Any:  # noqa: ANN401
        from nu import runtime
        from nu.terms.nu import NuBase

        if isinstance(val, NuBase):
            return await runtime.afirst(val, ctx)
        return val

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        from nu import runtime

        timeout = float(await self._resolve(ctx, self._timeout))
        try:
            return await asyncio.wait_for(call(), timeout=timeout)
        except TimeoutError:
            if self._on_timeout is not None:
                await runtime.aexecute(self._on_timeout, ctx)
                return None
            raise


class Throttle(Policy):
    """Drop body executions inside ``interval`` seconds of the prior run.

    Children: ``[body]``. ``interval`` kept on the instance.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, interval: FloatArg, body: Nu) -> None:
        super().__init__(body)
        self._interval = interval
        self._last_time: float = 0.0

    async def _resolve(self, ctx: Any, val: Any) -> Any:  # noqa: ANN401
        from nu import runtime
        from nu.terms.nu import NuBase

        if isinstance(val, NuBase):
            return await runtime.afirst(val, ctx)
        return val

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        interval = float(await self._resolve(ctx, self._interval))
        now = time.monotonic()
        if now - self._last_time < interval:
            return None
        self._last_time = now
        return await call()


class Debounce(Policy):
    """Delay body execution by ``delay``; cancel pending on re-entry.

    Children: ``[body]``. Each invocation cancels any in-flight task and
    starts a fresh timer.
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.ASYNC})

    def __init__(self, delay: FloatArg, body: Nu) -> None:
        super().__init__(body)
        self._delay = delay
        self._pending: asyncio.Task | None = None

    async def _resolve(self, ctx: Any, val: Any) -> Any:  # noqa: ANN401
        from nu import runtime
        from nu.terms.nu import NuBase

        if isinstance(val, NuBase):
            return await runtime.afirst(val, ctx)
        return val

    async def aaround(self, ctx: Any, call: Any) -> Any:  # noqa: ANN401
        delay = float(await self._resolve(ctx, self._delay))
        if self._pending is not None and not self._pending.done():
            self._pending.cancel()

        async def _later() -> Any:
            await asyncio.sleep(delay)
            return await call()

        self._pending = asyncio.create_task(_later())
        return None
