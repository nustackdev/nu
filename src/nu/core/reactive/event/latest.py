"""ReactLatest: run the body on every change, restarting it on a newer one."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.context.attrs.binders import bind
from nu.core.flows.parallel._scheduling import _settle
from nu.engine.structure import Declared
from nu.lang import Control

from .._body import async_only, changed, drain_body


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime

__all__ = ["ReactLatest"]


class ReactLatest(Control):
    """Run the body on every change, cancelling the run a newer change makes stale.

    ``ReactEvery`` with switch-latest semantics (Rx ``switchMap``). Binds to
    the change subscription once and starts the body as its own task on every
    notification. A run still going when the next notification lands is
    cancelled and awaited until it has fully unwound, and only then does the
    body start again with the newest key. Never returns on its own; the
    caller ends it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification: a lambda over the changed
            key, or a tree. May never finish (a live view, a server loop);
            the next change is what ends it.
        changed_key: name the changed key is bound under while each run of
            a tree body lasts; a lambda mints its own.
        initial: run the body once straight away, before any notification.
            That run binds no key, so the body sees whatever the caller
            seeded under ``changed_key``, or an unbound name (a lambda's key
            reads NULL).

    Notes:
        - Notifications that pile up while a cancelled run is unwinding are
          collapsed: only the newest key runs, the backlog is not replayed.
        - Each run gets a fresh branch of the Context it started from: its
          own attrs key space, values shared by reference. A restarted body
          never sees attrs a cancelled run left behind, and attrs a run binds
          do not reach the caller or its siblings.
        - A body that finishes on its own is fine; the flow just waits for
          the next change.
        - An error raised by the body, or while a cancelled run unwinds, ends
          the flow and propagates. The cancellation from a restart is not an
          error.
        - Cancelling the flow cancels and drains the running body before the
          subscription is unbound and closed.
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.

    Example:
        A live view restarted whenever a select moves, drawn once up front.
        Needs a real substrate behind the subscription, so it cannot run
        standalone::

            ReactLatest(
                Cell.source.on_change(),
                nustd.ui.lens.browse(Cell.lens, Movies),
                initial=True,
            )
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")

    def __init__(
        self,
        change: object,
        body: object,
        *,
        changed_key: object = None,
        initial: bool = False,
    ) -> None:
        body, (changed_key,) = bind("ReactLatest", body, changed_key=changed_key)
        has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)
        self._payload["has_changed_key"] = has_changed_key
        self._payload["initial"] = bool(initial)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactLatest")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_ck = self._payload["has_changed_key"]
        initial = self._payload["initial"]
        body = children[1]

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            changed_key_name = await children[2](rt) if has_ck else None

            def start(bind: bool, key: object = None) -> asyncio.Task:
                # Every run is a task of its own, on a fresh branch.
                run_rt = rt.branch()
                name = changed_key_name if bind else None

                async def run() -> None:
                    with changed(run_rt.ctx.attrs, name, key):
                        await drain_body(run_rt, body)

                return asyncio.ensure_future(run())

            running: asyncio.Task | None = None
            getter: asyncio.Task | None = None
            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                if initial:
                    running = start(bind=False)
                while True:
                    if getter is None:
                        getter = asyncio.ensure_future(queue.get())
                    waits = {getter} if running is None else {getter, running}
                    done, _ = await asyncio.wait(waits, return_when=asyncio.FIRST_COMPLETED)
                    # A run that ended on its own is checked first: its error
                    # wins over a notification that landed on the same tick.
                    if running is not None and running in done:
                        finished, running = running, None
                        finished.result()
                    if getter not in done:
                        continue
                    key, getter = getter.result(), None
                    if running is not None:
                        stale, running = running, None
                        await _settle([stale])
                        if not stale.cancelled():
                            stale.result()
                    # Whatever arrived while the stale run unwound is already
                    # queued; only the newest of it is worth a run.
                    while not queue.empty():
                        key = queue.get_nowait()
                    running = start(bind=True, key=key)
            finally:
                await _settle([t for t in (running, getter) if t is not None])
                sub.unbind(on_change)
                sub.close()

        return athunk
