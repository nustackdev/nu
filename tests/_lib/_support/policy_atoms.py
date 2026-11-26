"""Support atoms for Policy span tests (Retry, Timeout).

Each is a mutating atom that counts its own calls or records into an external
log or a declared name, so retry loops, hooks, and timeout cancellation are
all observable from a test. A counter or log is never kept on the term: it is
a live object held as data in a ``Literal`` child, the term only reads it.
A log is the test's list behind a ``Sink``: a plain list in a Literal would be
copied on every run, so the record would never reach the test.
"""

from __future__ import annotations

import asyncio
import itertools
from typing import TYPE_CHECKING

from nu.engine.structure import Declared
from nu.lang import Literal, ScalarAction, StreamQuery


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["FlakyAction", "FlakyStream", "RecordAction", "Sink", "SlowAction"]


class Sink:
    """The test's list behind an object a Literal hands out as is (hashable by identity).

    A recorder takes it as a child and gets it by running that child.
    """

    def __init__(self, log: list) -> None:
        self.log = log

    def append(self, item: object) -> None:
        self.log.append(item)


class FlakyAction(ScalarAction):
    """Fails its first ``fail_times`` calls (ValueError), then yields ``name``.

    Counts its calls in ``calls``, an ``itertools.count`` held as its one
    ``Literal`` child, so the count survives a retry loop's fresh re-runs.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fail_times: int, name: str = "flaky") -> None:
        super().__init__(Literal(itertools.count()))
        self._fail_times = fail_times
        self._name = name

    @property
    def calls(self) -> itertools.count:
        """The call counter, read off the ``Literal`` child."""
        return self._children[0].value

    def _run(self, rt: Runtime) -> object:
        n = next(self.calls)
        if n < self._fail_times:
            msg = f"flaky {n}"
            raise ValueError(msg)
        return self._name

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._run

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            return self._run(rt)

        return athunk


class RecordAction(ScalarAction):
    """Appends ``(tag, attempt, error)`` to an external log; yields None.

    Observes a hook firing and what it was handed: ``attempt`` / ``error`` are
    children, so a hook lambda passes its parameters in
    (``lambda err, attempt: RecordAction(log, "af", attempt=attempt, error=err)``).
    Left out, each records None.
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(
        self, log: list, tag: str = "rec", *, attempt: object = None, error: object = None
    ) -> None:
        super().__init__(Sink(log), attempt, error)
        self._tag = tag

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        sink, attempt, error = children

        def thunk(rt: Runtime) -> object:
            sink(rt).append((self._tag, attempt(rt), error(rt)))

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        sink, attempt, error = children

        async def athunk(rt: Runtime) -> object:
            (await sink(rt)).append((self._tag, await attempt(rt), await error(rt)))

        return athunk


class SlowAction(ScalarAction):
    """Async: sleep ``seconds``, set the declared ``name`` to True, yield ``name``.

    Sync thunk returns ``name`` without sleeping (never reached under an
    async-only span).
    """

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, seconds: float, name: str = "slow") -> None:
        super().__init__()
        self._seconds = seconds
        self._name = name

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        name = self._name

        def thunk(rt: Runtime) -> object:
            rt.ctx.attrs.set(name, True)
            return name

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        seconds = self._seconds
        name = self._name

        async def athunk(rt: Runtime) -> object:
            await asyncio.sleep(seconds)
            rt.ctx.attrs.set(name, True)
            return name

        return athunk


class FlakyStream(StreamQuery):
    """Stream that raises on its first ``fail_times`` calls, then yields ``items``.

    Counts its calls in a ``Literal`` child, so a retry re-runs it fresh each
    attempt.
    """

    def __init__(self, fail_times: int, items: object, name: str = "fs") -> None:
        super().__init__(Literal(itertools.count()))
        self._fail_times = fail_times
        self._items = list(items)
        self._name = name

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            n = next(self._children[0].value)
            fail_times = self._fail_times
            items = self._items

            def gen() -> object:
                if n < fail_times:
                    msg = f"fs {n}"
                    raise ValueError(msg)
                yield from items

            return gen()

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            n = next(self._children[0].value)
            fail_times = self._fail_times
            items = self._items

            async def agen() -> object:
                if n < fail_times:
                    msg = f"fs {n}"
                    raise ValueError(msg)
                for item in items:
                    yield item

            return agen()

        return athunk
