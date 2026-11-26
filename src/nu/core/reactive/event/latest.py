"""ReactLatest: run the body on every change, restarting it on a newer one."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.core.flows.parallel._scheduling import _settle
from nu.engine.structure import Declared
from nu.lang import Control
from nu.lang.binding import Binding

from .._body import async_only, drain_body


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import BoolArg
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
            key, or a tree that reads none. May never finish (a live view, a
            server loop); the next change is what ends it.
        initial: run the body once straight away, before any notification:
            a bool, or any Nu yielding one, evaluated when the flow starts
            (the last child). That run has no key: a lambda's key reads
            NULL.

    Notes:
        - Notifications that pile up while a cancelled run is unwinding are
          collapsed: only the newest key runs, the backlog is not replayed.
        - Each run pushes its own frame on the reaction's frames, holding
          its key, values shared by reference. A restarted body never sees a
          frame a cancelled run pushed, and a frame a run pushes never
          reaches the caller or its siblings.
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

    def __init__(self, change: object, body: object, *, initial: BoolArg = False) -> None:
        body, self._binding = Binding.of_lambda("ReactLatest", body, 1)
        super().__init__(change, body, initial)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        return async_only("ReactLatest")

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        body, initial_t = children[1], children[2]  # [change, body, initial]
        binding = self._binding

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            def start(bind: bool, key: object = None) -> asyncio.Task:
                # Every run is a task of its own on a frame of its own; the
                # initial run's frame holds no key, so a lambda's reads NULL.
                run_ctx = binding.push(rt.ctx, key) if bind else binding.push(rt.ctx)
                return asyncio.ensure_future(drain_body(rt.on(run_ctx), body))

            running: asyncio.Task | None = None
            getter: asyncio.Task | None = None
            initial = await initial_t(rt)
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
