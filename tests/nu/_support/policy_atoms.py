"""Support atoms for Policy span tests (Retry, Timeout, Throttle, Debounce).

Each is a childless mutating atom that counts/records through ``ctx.attrs`` or an
external log, so retry loops, hooks (which run in an isolated ctx copy), timeout
cancellation, and throttle/debounce state are all observable from a test.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import ScalarAction, StreamQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["CountAction", "FlakyAction", "FlakyStream", "RecordAction", "SlowAction"]


class FlakyAction(ScalarAction):
    """Fails its first ``fail_times`` calls (ValueError), then yields ``name``.

    Counts calls in ``ctx.attrs`` so it survives a retry loop's fresh re-runs.
    """

    mutates = Declared(value=frozenset({0}))

    def __init__(self, fail_times: int, name: str = "flaky") -> None:
        super().__init__()
        self.payload["fail_times"] = fail_times
        self.payload["name"] = name

    def _run(self, rt: Runtime) -> object:
        key = f"__flaky_calls_{self.payload['name']}__"
        n = rt.ctx.attrs.get(key, 0)
        rt.ctx.attrs[key] = n + 1
        if n < self.payload["fail_times"]:
            msg = f"flaky {n}"
            raise ValueError(msg)
        return self.payload["name"]

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._run

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._run(rt)

        return athunk


class RecordAction(ScalarAction):
    """Appends ``(tag, attempt, error)`` to an external log; yields None.

    Observes a hook firing even though hooks run against an isolated ctx copy -
    the log is external, not ctx.
    """

    mutates = Declared(value=frozenset({0}))

    def __init__(self, log: list, tag: str = "rec") -> None:
        super().__init__()
        self.payload["log"] = log
        self.payload["tag"] = tag

    def _run(self, rt: Runtime) -> object:
        self.payload["log"].append(
            (self.payload["tag"], rt.ctx.attrs.get("attempt"), rt.ctx.attrs.get("error")),
        )
        return None

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._run

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._run(rt)

        return athunk


class CountAction(ScalarAction):
    """Increments ``ctx.attrs[key]`` each run; yields the new count."""

    mutates = Declared(value=frozenset({0}))

    def __init__(self, key: str = "count") -> None:
        super().__init__()
        self.payload["key"] = key

    def _run(self, rt: Runtime) -> object:
        key = self.payload["key"]
        n = rt.ctx.attrs.get(key, 0) + 1
        rt.ctx.attrs[key] = n
        return n

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._run

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._run(rt)

        return athunk


class SlowAction(ScalarAction):
    """Async: sleep ``seconds``, write ``attrs[name]=True``, yield ``name``.

    Sync thunk returns ``name`` without sleeping (never reached under an
    async-only span).
    """

    mutates = Declared(value=frozenset({0}))

    def __init__(self, seconds: float, name: str = "slow") -> None:
        super().__init__()
        self.payload["seconds"] = seconds
        self.payload["name"] = name

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self.payload["name"]

        def thunk(rt: Runtime) -> object:
            rt.ctx.attrs[name] = True
            return name

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        seconds = self.payload["seconds"]
        name = self.payload["name"]

        async def athunk(rt: Runtime) -> object:
            await asyncio.sleep(seconds)
            rt.ctx.attrs[name] = True
            return name

        return athunk


class FlakyStream(StreamQuery):
    """Stream that raises on its first ``fail_times`` calls, then yields ``items``.

    Counts calls in ``ctx.attrs`` so a retry re-runs it fresh each attempt.
    """

    def __init__(self, fail_times: int, items: object, name: str = "fs") -> None:
        super().__init__()
        self.payload["fail_times"] = fail_times
        self.payload["items"] = list(items)
        self.payload["name"] = name

    def compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            key = f"__fs_calls_{self.payload['name']}__"
            n = rt.ctx.attrs.get(key, 0)
            rt.ctx.attrs[key] = n + 1
            fail_times = self.payload["fail_times"]
            items = self.payload["items"]

            def gen() -> object:
                if n < fail_times:
                    msg = f"fs {n}"
                    raise ValueError(msg)
                yield from items

            return gen()

        return thunk

    def acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            key = f"__fs_calls_{self.payload['name']}__"
            n = rt.ctx.attrs.get(key, 0)
            rt.ctx.attrs[key] = n + 1
            fail_times = self.payload["fail_times"]
            items = self.payload["items"]

            async def agen() -> object:
                if n < fail_times:
                    msg = f"fs {n}"
                    raise ValueError(msg)
                for item in items:
                    yield item

            return agen()

        return athunk
