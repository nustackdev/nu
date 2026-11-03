"""virtuals' keyless resync wake reaches nu flows as ``RESYNC``.

virtuals calls a receiver with ``None`` after a reconnect, meaning "re-read
state". The kv observers turn it into nu's ``RESYNC`` marker: a level flow
runs a pass on it, an event flow skips it and still fires on real keys.
"""

from __future__ import annotations

import asyncio
import pickle
from typing import TYPE_CHECKING

import pytest

from nu.context import Attr
from nu.core.reactive import RESYNC, ObserverProtocol, ReactForever, ReconcileReactive
from nu.engine.structure import Declared
from nu.lang import Context, ScalarAction
from nu.lang.helpers import arun
from nustd.kv.fabrics import Codec, InMemoryObserver, InMemoryTransport, binary_kwargs
from virtuals.tkv.filter import PrefixFilter
from virtuals.tkv.observer import SubscriptionOptions


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


PREFIX = ("demo",)


class _Held:
    """The subscription as a ctx attr, kept one object across scope copies."""

    def __init__(self, sub: object) -> None:
        self.sub = sub

    def __deepcopy__(self, memo: dict) -> _Held:
        return self

    def bind(self, receiver: Callable) -> None:
        self.sub.bind(receiver)

    def unbind(self, receiver: Callable) -> None:
        self.sub.unbind(receiver)

    def close(self) -> None:
        self.sub.close()


class _Body(ScalarAction):
    _requires_async = Declared(value=True, name="requires_async")
    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "_Body was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return await fn(rt)

        return athunk


def _observer() -> InMemoryObserver:
    ctx = Context().bind(Codec, Codec(**binary_kwargs()))
    transport = InMemoryTransport()
    transport.setup(ctx)
    observer = InMemoryObserver()
    observer.setup(ctx.bind(InMemoryTransport, transport))
    return observer


async def _until(check: Callable[[], bool], timeout: float = 5.0) -> None:
    async def poll() -> None:
        while not check():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(poll(), timeout)


async def _stop(task: asyncio.Task) -> None:
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


def test_the_marker_survives_pickling():
    assert pickle.loads(pickle.dumps(RESYNC)) is RESYNC  # noqa: S301 -- our own bytes


def test_kv_observers_bind_under_the_protocol():
    assert InMemoryObserver._nu_bind_as is ObserverProtocol


async def test_a_none_wake_reaches_a_level_flow_as_a_reread_and_an_event_flow_skips_it():
    observer = _observer()
    try:
        level_sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=PREFIX)))
        event_sub = observer.subscribe(SubscriptionOptions(filter=PrefixFilter(prefix=PREFIX)))
        passes: list[int] = []
        keys: list[object] = []

        async def level(rt: Runtime) -> None:
            passes.append(len(passes))

        async def event(rt: Runtime) -> None:
            keys.append(rt.ctx.attrs.get("k"))

        level_task = asyncio.ensure_future(
            arun(
                ReconcileReactive(Attr("level"), _Body(level), after=(), every=None),
                Context(attrs={"level": _Held(level_sub)}),
            )
        )
        event_task = asyncio.ensure_future(
            arun(
                ReactForever(Attr("event"), _Body(event), changed_key="k"),
                Context(attrs={"event": _Held(event_sub)}),
            )
        )
        await _until(lambda: passes == [0])  # the bind wake
        await asyncio.sleep(0.05)  # let the event flow bind too

        observer._dispatch_resync(level_sub.filter_hash)
        observer._dispatch_resync(event_sub.filter_hash)
        await _until(lambda: len(passes) == 2)
        await asyncio.sleep(0.05)
        assert keys == []

        observer._dispatch_incoming([("demo", "x")])
        await _until(lambda: keys == [("demo", "x")])
        await _until(lambda: len(passes) == 3)

        await _stop(level_task)
        await _stop(event_task)
    finally:
        observer.cleanup()
