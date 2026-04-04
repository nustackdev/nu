"""Reactive flows -- React, ReactForever, ReactWhile.

Subscribe to change events and execute children in response.
Uses ``ChangeOp`` ops from nu.shape to obtain subscription
handles, then bridges callback-based notifications into async via
``asyncio.Event``.

React:         Wait for a single change, optionally execute body once.
ReactForever:  Execute body on every change (runs forever).
ReactWhile:    Execute body on each change while condition is truthy.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from nu import Flow
from nu.utils import ensure_nu

from ..ops import ChangeOp  # noqa: TC001 - runtime dependency


if TYPE_CHECKING:
    from nu import Context, Nu
    from nu.terms import StrArg


__all__ = [
    "React",
    "ReactForever",
    "ReactWhile",
]


class React(Flow):
    """Wait for a single change, then execute body once.

    Children layout: ``[change, body?, changed_key?]``

    Subscribes via the ``ChangeOp`` child to obtain a subscription
    handle. Waits for the first change event, optionally stores the
    changed key into ``ctx.attrs[changed_key]``, then executes the
    optional body child and unsubscribes.

    Example::

        React(user.on_change(), handle_change)
        React(config.on_change())  # just wait, no action
        React(
            items.on_children_change(),
            process_item,
            changed_key="changed_key",
        )
    """

    def __init__(
        self,
        change: ChangeOp,
        body: Nu | None = None,
        *,
        changed_key: StrArg | None = None,
    ) -> None:
        """Initialize single-shot reactive flow.

        Args:
            change: ChangeOp that produces a subscription handle.
            body: Optional Nu run after the first change event.
            changed_key: ctx.attrs key written with the key that changed.
        """
        self._has_changed_key = changed_key is not None
        children: list = [change]
        if body is not None:
            children.append(body)
        self._body_idx = 1 if body is not None else None
        if changed_key is not None:
            self._changed_key_idx = len(children)
            children.append(ensure_nu(changed_key))
        else:
            self._changed_key_idx = None
        super().__init__(*children)

    async def execute(self, ctx: Context) -> None:
        """Subscribe, wait for one change, run body, unsubscribe."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()
        changed_key_holder: list[object] = [None]

        def on_change(changed_key: object) -> None:
            changed_key_holder[0] = changed_key
            loop.call_soon_threadsafe(event.set)

        changed_key_name: str | None = None
        if self._changed_key_idx is not None:
            changed_key_name = await self.children[self._changed_key_idx].execute(ctx)

        sub = await self.children[0].execute(ctx)
        sub.bind(on_change)
        try:
            await event.wait()

            if changed_key_name is not None:
                ctx.attrs[changed_key_name] = changed_key_holder[0]

            if self._body_idx is not None:
                await self.children[self._body_idx].execute(ctx)
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactForever(Flow):
    """Execute body on every change (runs forever).

    Children layout: ``[change, body, changed_key?]``

    Subscribes via the ``ChangeOp`` child and loops indefinitely,
    waiting for each change event. On every event, optionally stores
    the changed key into ``ctx.attrs[changed_key]``, then executes the
    body child. Only terminates via exception or task cancellation.

    Example::

        ReactForever(
            tasks.on_children_change(),
            sync_task,
        )
        ReactForever(
            events.on_descendants_change("*", "status"),
            process_status,
            changed_key="changed_key",
        )
    """

    def __init__(
        self,
        change: ChangeOp,
        body: Nu,
        *,
        changed_key: StrArg | None = None,
    ) -> None:
        """Initialize forever-reactive flow.

        Args:
            change: ChangeOp that produces a subscription handle.
            body: Nu run after every change event.
            changed_key: ctx.attrs key written with the key that changed.
        """
        self._has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, body, ensure_nu(changed_key))
        else:
            super().__init__(change, body)

    async def execute(self, ctx: Context) -> None:
        """Subscribe, loop forever reacting to changes, unsubscribe on exit."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()
        changed_key_holder: list[object] = [None]

        def on_change(changed_key: object) -> None:
            changed_key_holder[0] = changed_key
            loop.call_soon_threadsafe(event.set)

        changed_key_name: str | None = None
        if self._has_changed_key:
            changed_key_name = await self.children[2].execute(ctx)

        sub = await self.children[0].execute(ctx)
        sub.bind(on_change)
        try:
            while True:
                await event.wait()
                event.clear()

                if changed_key_name is not None:
                    ctx.attrs[changed_key_name] = changed_key_holder[0]

                await self.children[1].execute(ctx)
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactWhile(Flow):
    """Execute body on each change while condition is truthy.

    Children layout: ``[change, condition, body, changed_key?]``

    Subscribes via the ``ChangeOp`` child and loops, waiting for
    each change event. After every event the condition child is
    evaluated; if falsy the loop breaks and the subscription is
    torn down. Otherwise the changed key is optionally stored and
    the body child is executed.

    Condition is auto-wrapped via ``ensure_nu`` if a literal is passed.

    Example::

        ReactWhile(
            queue.on_children_change(),
            queue_active_flag,
            process_item,
        )
        ReactWhile(
            sensor.on_change(),
            True,
            log_reading,
            changed_key="sensor_key",
        )
    """

    def __init__(
        self,
        change: ChangeOp,
        condition: Any,
        body: Nu,
        *,
        changed_key: StrArg | None = None,
    ) -> None:
        """Initialize conditional-reactive flow.

        Args:
            change: ChangeOp that produces a subscription handle.
            condition: Nu or literal evaluated after each event. Loop
                continues while truthy. Literals are wrapped via ``ensure_nu``.
            body: Nu run after each change while condition holds.
            changed_key: ctx.attrs key written with the key that changed.
        """
        self._has_changed_key = changed_key is not None
        if changed_key is not None:
            super().__init__(change, ensure_nu(condition), body, ensure_nu(changed_key))
        else:
            super().__init__(change, ensure_nu(condition), body)

    async def execute(self, ctx: Context) -> None:
        """Subscribe, react while condition holds, unsubscribe on exit."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()
        changed_key_holder: list[object] = [None]

        def on_change(changed_key: object) -> None:
            changed_key_holder[0] = changed_key
            loop.call_soon_threadsafe(event.set)

        changed_key_name: str | None = None
        if self._has_changed_key:
            changed_key_name = await self.children[3].execute(ctx)

        sub = await self.children[0].execute(ctx)
        sub.bind(on_change)
        try:
            while True:
                await event.wait()
                event.clear()

                if not await self.children[1].execute(ctx):
                    break

                if changed_key_name is not None:
                    ctx.attrs[changed_key_name] = changed_key_holder[0]

                await self.children[2].execute(ctx)
        finally:
            sub.unbind(on_change)
            sub.close()
