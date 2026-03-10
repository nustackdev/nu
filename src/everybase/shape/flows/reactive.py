"""Reactive flows -- React, ReactForever, ReactWhile.

Subscribe to change events and execute children in response.
Uses ``ChangeOp`` morphisms from everybase.shape to obtain subscription
handles, then bridges callback-based notifications into async via
``asyncio.Event``.

React:         Wait for a single change, optionally execute body once.
ReactForever:  Execute body on every change (runs forever).
ReactWhile:    Execute body on each change while condition is truthy.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from everybase import Flow
from everybase.abc import ensure_term

from ..morphisms import ChangeOp  # noqa: TC001 - runtime dependency


if TYPE_CHECKING:
    from everybase import Context, Executable, Ref


__all__ = [
    "React",
    "ReactForever",
    "ReactWhile",
]


class React(Flow):
    """Wait for a single change, then execute body once.

    Children layout: ``[change, body?]``

    Subscribes via the ``ChangeOp`` child to obtain a subscription
    handle. Waits for the first change event, optionally stores the
    changed key into the ``changed_key`` Ref, then executes the
    optional body child and unsubscribes.

    Example::

        React(user.on_change(), handle_change)
        React(config.on_change())  # just wait, no action
        React(
            items.on_children_change(),
            process_item,
            changed_key=key_ref,
        )
    """

    def __init__(
        self,
        change: ChangeOp,
        body: Executable | None = None,
        *,
        changed_key: Ref | None = None,
    ) -> None:
        """Initialize single-shot reactive flow.

        Args:
            change: ChangeOp morphism that produces a subscription handle.
            body: Optional executable run after the first change event.
            changed_key: Optional Ref written with the key that changed.
                Not a child -- stored as metadata only.
        """
        if body is not None:
            super().__init__(change, body)
        else:
            super().__init__(change)
        self._changed_key = changed_key

    async def execute(self, ctx: Context) -> None:
        """Subscribe, wait for one change, run body, unsubscribe."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()
        changed_key_holder: list[object] = [None]

        def on_change(changed_key: object) -> None:
            changed_key_holder[0] = changed_key
            loop.call_soon_threadsafe(event.set)

        sub = await self.children[0].execute(ctx)
        sub.bind(on_change)
        try:
            await event.wait()

            if self._changed_key is not None:
                await self._changed_key.store(changed_key_holder[0]).execute(ctx)  # type: ignore[union-attr]

            if self.child_count > 1:
                await self.children[1].execute(ctx)
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactForever(Flow):
    """Execute body on every change (runs forever).

    Children layout: ``[change, body]``

    Subscribes via the ``ChangeOp`` child and loops indefinitely,
    waiting for each change event. On every event, optionally stores
    the changed key into the ``changed_key`` Ref, then executes the
    body child. Only terminates via exception or task cancellation.

    Example::

        ReactForever(
            tasks.on_children_change(),
            sync_task,
        )
        ReactForever(
            events.on_descendants_change("*", "status"),
            process_status,
            changed_key=key_ref,
        )
    """

    def __init__(
        self,
        change: ChangeOp,
        body: Executable,
        *,
        changed_key: Ref | None = None,
    ) -> None:
        """Initialize forever-reactive flow.

        Args:
            change: ChangeOp morphism that produces a subscription handle.
            body: Executable run after every change event.
            changed_key: Optional Ref written with the key that changed.
                Not a child -- stored as metadata only.
        """
        super().__init__(change, body)
        self._changed_key = changed_key

    async def execute(self, ctx: Context) -> None:
        """Subscribe, loop forever reacting to changes, unsubscribe on exit."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()
        changed_key_holder: list[object] = [None]

        def on_change(changed_key: object) -> None:
            changed_key_holder[0] = changed_key
            loop.call_soon_threadsafe(event.set)

        sub = await self.children[0].execute(ctx)
        sub.bind(on_change)
        try:
            while True:
                await event.wait()
                event.clear()

                if self._changed_key is not None:
                    await self._changed_key.store(changed_key_holder[0]).execute(ctx)  # type: ignore[union-attr]

                await self.children[1].execute(ctx)
        finally:
            sub.unbind(on_change)
            sub.close()


class ReactWhile(Flow):
    """Execute body on each change while condition is truthy.

    Children layout: ``[change, condition, body]``

    Subscribes via the ``ChangeOp`` child and loops, waiting for
    each change event. After every event the condition child is
    evaluated; if falsy the loop breaks and the subscription is
    torn down. Otherwise the changed key is optionally stored and
    the body child is executed.

    Condition is auto-wrapped via ``ensure_term`` if a literal is passed.

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
            changed_key=sensor_key,
        )
    """

    def __init__(
        self,
        change: ChangeOp,
        condition: Any,
        body: Executable,
        *,
        changed_key: Ref | None = None,
    ) -> None:
        """Initialize conditional-reactive flow.

        Args:
            change: ChangeOp morphism that produces a subscription handle.
            condition: Term or literal evaluated after each event. Loop
                continues while truthy. Literals are wrapped via ``ensure_term``.
            body: Executable run after each change while condition holds.
            changed_key: Optional Ref written with the key that changed.
                Not a child -- stored as metadata only.
        """
        super().__init__(change, ensure_term(condition), body)
        self._changed_key = changed_key

    async def execute(self, ctx: Context) -> None:
        """Subscribe, react while condition holds, unsubscribe on exit."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()
        changed_key_holder: list[object] = [None]

        def on_change(changed_key: object) -> None:
            changed_key_holder[0] = changed_key
            loop.call_soon_threadsafe(event.set)

        sub = await self.children[0].execute(ctx)
        sub.bind(on_change)
        try:
            while True:
                await event.wait()
                event.clear()

                if not await self.children[1].execute(ctx):
                    break

                if self._changed_key is not None:
                    await self._changed_key.store(changed_key_holder[0]).execute(ctx)  # type: ignore[union-attr]

                await self.children[2].execute(ctx)
        finally:
            sub.unbind(on_change)
            sub.close()
