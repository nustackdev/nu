"""Reactive control flows: React, ReactWhile, ReactForever, ReactLatest.

Subscribe to a change event and run a body in response. All four are
``Control`` flows: they drive a mutating body under query parameters (a
change subscription, a condition) and yield nothing, exactly like ``WhileDo``
/ ``ForeverDo``. A change notification is bridged into async via
``asyncio.Queue``, so all four require an async runtime and raise from their
sync ``_compile`` path. The first three take one wake per notification with
no collapsing; ``ReactLatest`` collapses a backlog to its newest key, since
it only ever runs the latest one.

``param_slots`` names the consumed queries (the change subscription at slot
0, a condition where present, an optional ``changed_key`` name); the
remaining slot is the body.
"""

from __future__ import annotations

import asyncio
from contextlib import nullcontext
from typing import TYPE_CHECKING

from nu.core._stream import aiter_any
from nu.engine.structure import Declared
from nu.lang import Control


if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager

    from nu.lang.runtime import Runtime
    from nu.lang.runtime.context import Attributes

__all__ = ["React", "ReactForever", "ReactLatest", "ReactWhile"]


async def _adrain_body(rt: Runtime, body_thunk: Callable) -> None:
    """Run a react body once and pull any values it yields through to completion.

    Args:
        rt: the runtime to run the body under.
        body_thunk: the compiled body thunk to await.

    Notes:
        - A body may be a Command (returns ``None``) or a stream (returns an
          iterable / async-iterable). Commands carry their writes and stop
          here; a stream's values must be drained to fire the side effects
          riding along with them, since nothing else pulls on them.

    Yields:
        Nothing. Always returns ``None``.
    """
    result = await body_thunk(rt)
    if result is None:
        return
    async for _ in aiter_any(result):
        pass


def _changed(attrs: Attributes, name: object, key: object) -> AbstractContextManager:
    """The scope a body run sees the changed key in: ``key`` bound under ``name``.

    Binds nothing when the flow was given no ``changed_key``.
    """
    return nullcontext() if name is None else attrs.let(name, key)


class React(Control):
    """Wait for one change on the subscription, run the body once, then stop.

    Binds to the change subscription, blocks until exactly one notification
    arrives, unbinds, and closes the subscription. The body (when present)
    runs once, after that single notification, before ``React`` returns.

    Args:
        change: the change subscription to wait on (a ``Subscription``-yielding
            query, e.g. ``OnChange``).
        body: what to run once the change fires. Optional: leave it out to
            just wait for one change and do nothing.
        changed_key: name the changed key is bound under while the body
            runs. Requires a body.

    Notes:
        - Requires a body when ``changed_key`` is given: capturing a key with
          nothing to run it against is meaningless.
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 2}), name="param_slots")

    def __init__(
        self,
        change: object,
        body: object = None,
        *,
        changed_key: object = None,
    ) -> None:
        if changed_key is not None and body is None:
            msg = "React changed_key requires a body"
            raise ValueError(msg)
        children: list = [change]
        if body is not None:
            children.append(body)
        if changed_key is not None:
            children.append(changed_key)
        super().__init__(*children)
        self._payload["has_body"] = body is not None
        self._payload["has_changed_key"] = changed_key is not None

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "React requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_body = self._payload["has_body"]
        ck_idx = 2 if self._payload["has_changed_key"] else None

        async def athunk(rt: Runtime) -> None:
            changed_key_name = await children[ck_idx](rt) if ck_idx is not None else None
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                key = await queue.get()
                if has_body:
                    with _changed(rt.ctx.attrs, changed_key_name, key):
                        await _adrain_body(rt, children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk


class ReactWhile(Control):
    """Run the body on each change while the condition stays truthy.

    Binds to the change subscription once, then on every notification checks
    the condition first: false stops the loop and unbinds without running the
    body for that notification; truthy runs the body and waits for the next
    change. The condition is re-evaluated fresh on every notification, not
    just once at the start.

    Args:
        change: the change subscription to wait on.
        condition: checked after each notification, before that turn's body
            runs. A falsy value ends the loop.
        body: what to run on a turn where the condition holds.
        changed_key: name the changed key is bound under while that turn's
            body runs.

    Notes:
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.
    """

    _mutates = Declared(value=frozenset(), name="mutates")
    _requires_async = Declared(value=True, name="requires_async")
    _param_slots = Declared(value=frozenset({0, 1, 3}), name="param_slots")

    def __init__(
        self,
        change: object,
        condition: object,
        body: object,
        *,
        changed_key: object = None,
    ) -> None:
        has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, condition, body, changed_key)
        else:
            super().__init__(change, condition, body)
        self._payload["has_changed_key"] = has_changed_key

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ReactWhile requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_ck = self._payload["has_changed_key"]

        async def athunk(rt: Runtime) -> None:
            changed_key_name = await children[3](rt) if has_ck else None
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await queue.get()
                    if not await children[1](rt):
                        break
                    with _changed(rt.ctx.attrs, changed_key_name, key):
                        await _adrain_body(rt, children[2])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk


class ReactForever(Control):
    """Run the body on every change, unconditionally, forever.

    Binds to the change subscription once and then runs the body once per
    notification, with no condition to end the loop. Never returns on its
    own; the caller ends it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification.
        changed_key: name the changed key is bound under while each body
            run lasts.

    Notes:
        - Requires an async runtime; the sync path raises ``RuntimeError``.

    Yields:
        Nothing.
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
    ) -> None:
        has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)
        self._payload["has_changed_key"] = has_changed_key

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ReactForever requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        has_ck = self._payload["has_changed_key"]

        async def athunk(rt: Runtime) -> None:
            loop = asyncio.get_running_loop()
            queue: asyncio.Queue[object] = asyncio.Queue()

            def on_change(k: object) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, k)

            changed_key_name = await children[2](rt) if has_ck else None
            sub = await children[0](rt)
            sub.bind(on_change)
            try:
                while True:
                    key = await queue.get()
                    with _changed(rt.ctx.attrs, changed_key_name, key):
                        await _adrain_body(rt, children[1])
            finally:
                sub.unbind(on_change)
                sub.close()

        return athunk


class ReactLatest(Control):
    """Run the body on every change, cancelling the run a newer change makes stale.

    ``ReactForever`` with switch-latest semantics (Rx ``switchMap``). Binds to
    the change subscription once and starts the body as its own task on every
    notification. A run still going when the next notification lands is
    cancelled and awaited until it has fully unwound, and only then does the
    body start again with the newest key. Never returns on its own; the
    caller ends it by cancelling the surrounding task.

    Args:
        change: the change subscription to wait on.
        body: what to run on every notification. May never finish (a live
            view, a server loop); the next change is what ends it.
        changed_key: name the changed key is bound under while each body
            run lasts.
        initial: run the body once straight away, before any notification.
            That run binds nothing under ``changed_key``, so the body sees
            whatever the caller seeded there, or an unbound slot.

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
        has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, changed_key)
        else:
            super().__init__(change, body)
        self._payload["has_changed_key"] = has_changed_key
        self._payload["initial"] = bool(initial)

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> None:
            msg = "ReactLatest requires an async runtime; use arun"
            raise RuntimeError(msg)

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        from .parallel._scheduling import _settle

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
                    with _changed(run_rt.ctx.attrs, name, key):
                        await _adrain_body(run_rt, body)

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
