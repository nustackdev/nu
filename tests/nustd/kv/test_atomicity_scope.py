"""Snapshot and Transaction as scopes on the task's fabrics store.

A kv bracket provides its handle on ``ctx.fabrics`` for its body and for
nothing else: not after the body, not to a sibling arm, and it commits or
aborts on the way out.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.context import With
from nu.core.flows import Parallel
from nu.core.spans import TryCatch
from nu.engine.structure import Declared
from nu.lang import ScalarAction
from nu.lang.helpers import arun, run
from nustd.kv import Snapshot, Transaction, memory_navigator
from virtuals import Navigator
from virtuals.tkv.storage import SnapshotProtocol, TransactionProtocol


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


KEY = ("atomicity", "k")


class _Fn(ScalarAction):
    """Runs a plain ``fn(rt)`` on either path."""

    _mutates = Declared(value=frozenset({0}), name="mutates")

    def __init__(self, fn: Callable) -> None:
        super().__init__()
        self._payload["fn"] = fn

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._payload["fn"]

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        fn = self._payload["fn"]

        async def athunk(rt: Runtime) -> object:
            return fn(rt)

        return athunk


class _AsyncFn(_Fn):
    """Awaits a coroutine ``fn(rt)``; async-only."""

    _requires_async = Declared(value=True, name="requires_async")

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            msg = "_AsyncFn was placed on the sync path"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return self._payload["fn"]


def _stored(seen: dict) -> _Fn:
    """Record whether KEY landed in storage, read outside any bracket."""

    def fn(rt: Runtime) -> None:
        with rt.ctx.fabrics.get(Navigator).storage.snapshot() as view:
            seen["stored"] = view.exists(KEY)

    return _Fn(fn)


def test_transaction_is_provided_for_its_body_only() -> None:
    seen: dict = {}

    def write(rt: Runtime) -> None:
        rt.ctx.fabrics.get(TransactionProtocol).put(KEY, 1)
        seen["inside"] = rt.ctx.fabrics.has(TransactionProtocol)

    def after(rt: Runtime) -> None:
        seen["after"] = rt.ctx.fabrics.has(TransactionProtocol)

    run(With(memory_navigator(), body=Transaction(_Fn(write)) >> _Fn(after) >> _stored(seen)))
    assert seen == {"inside": True, "after": False, "stored": True}


def test_transaction_aborts_when_the_body_raises() -> None:
    seen: dict = {}

    def write(rt: Runtime) -> None:
        rt.ctx.fabrics.get(TransactionProtocol).put(KEY, 1)
        raise ValueError("boom")

    def after(rt: Runtime) -> None:
        seen["after"] = rt.ctx.fabrics.has(TransactionProtocol)

    guarded = TryCatch(Transaction(_Fn(write)), catch=_Fn(lambda rt: seen.update(caught=True)))
    run(With(memory_navigator(), body=guarded >> _Fn(after) >> _stored(seen)))
    assert seen == {"caught": True, "after": False, "stored": False}


def test_snapshot_is_provided_for_its_body_only() -> None:
    seen: dict = {}

    def read(rt: Runtime) -> None:
        rt.ctx.fabrics.get(SnapshotProtocol).get(KEY)
        seen["inside"] = rt.ctx.fabrics.was_opened(SnapshotProtocol)

    def after(rt: Runtime) -> None:
        seen["after"] = rt.ctx.fabrics.has(SnapshotProtocol)

    run(With(memory_navigator(), body=Snapshot(_Fn(read)) >> _Fn(after)))
    assert seen == {"inside": True, "after": False}


async def test_a_sibling_arm_never_sees_the_other_arms_transaction() -> None:
    seen: dict = {}
    opened, looked = asyncio.Event(), asyncio.Event()

    async def write(rt: Runtime) -> None:
        rt.ctx.fabrics.get(TransactionProtocol).put(KEY, 1)
        opened.set()
        await looked.wait()

    async def look(rt: Runtime) -> None:
        await opened.wait()
        seen["sibling"] = rt.ctx.fabrics.has(TransactionProtocol)
        looked.set()

    tree = With(
        memory_navigator(),
        body=Parallel(Transaction(_AsyncFn(write)), _AsyncFn(look)) >> _stored(seen),
    )
    await arun(tree)
    assert seen == {"sibling": False, "stored": True}
