"""Reactive Flow implementations.

This module provides reactive flows that subscribe to changes and execute
child flows in response:

- React: Wait for a single change, then execute child
- ReactForever: Execute child on every change (runs forever)
- ReactWhile: Execute child on every change while condition is true
"""

from __future__ import annotations

import asyncio
import threading

import attrs

from everyabc import Flow, Morphism, Runtime, Term


__all__ = [
    "React",
    "ReactForever",
    "ReactWhile",
]

type Key = tuple[str | int]

# TODO: update once reactive morphisms are there
type ChangeOp = Morphism


@attrs.define
class _React[RuntimeT: Runtime](Flow[RuntimeT]):
    """Wait for a single change, then execute child.

    Subscribes using the provided ChangeOp, waits for the first change,
    then executes the child flow once and completes.

    Flow Building Pattern:
        The changed key is available via runtime.attributes as "changed_key".
        This allows child flows to know what changed.

    Use cases:
        - Wait for initialization to complete
        - Gate execution until data is available
        - One-time event handling
    """

    change: ChangeOp = attrs.field()
    child: Flow | Term | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Wait for change, then execute child."""
        change_event = threading.Event()
        changed_key_holder: dict[str, Key] = {}
        lock = threading.Lock()

        def on_change(changed_key: Key) -> None:
            with lock:
                changed_key_holder["key"] = changed_key
                change_event.set()

        sub = runtime.terms.execute_term(self.change)

        try:
            loop = asyncio.get_running_loop()

            with sub(on_change):
                while not change_event.is_set():
                    runtime.cancellation.terminate_cancelled(runtime.path)
                    await loop.run_in_executor(None, change_event.wait, 0.1)

                with lock:
                    changed_key = changed_key_holder.get("key", ())

                if self.child is not None:
                    runtime.attributes.set(
                        runtime.path,
                        "changed_key",
                        changed_key,
                        step_name=self.name,
                    )
                    await self.execute_child(self.child, 0, runtime)
        finally:
            sub.close()


@attrs.define
class _ReactForever[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child on every change (runs forever).

    Subscribes using the provided ChangeOp and executes the child flow
    each time a change is detected. Runs indefinitely until cancelled.

    Flow Building Pattern:
        The changed key is available via runtime.attributes as "changed_key".
        This allows child flows to know what changed.

    Use cases:
        - Real-time data synchronization
        - Event-driven processing
        - Continuous monitoring
    """

    change: ChangeOp = attrs.field()
    child: Flow | Term | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child on each change forever."""
        if not self.child:
            raise ValueError("No child is provided")

        change_event = threading.Event()
        changed_key_holder: dict[str, Key] = {}
        lock = threading.Lock()

        def on_change(changed_key: Key) -> None:
            with lock:
                changed_key_holder["key"] = changed_key
                change_event.set()

        sub = runtime.terms.execute_term(self.change)

        try:
            loop = asyncio.get_running_loop()

            with sub(on_change):
                while True:
                    runtime.cancellation.terminate_cancelled(runtime.path)

                    await loop.run_in_executor(None, change_event.wait, 0.1)

                    if not change_event.is_set():
                        continue

                    with lock:
                        changed_key = changed_key_holder.get("key", ())
                        change_event.clear()

                    runtime.attributes.set(
                        runtime.path,
                        "changed_key",
                        changed_key,
                        step_name=self.name,
                    )

                    await self.execute_child(self.child, 0, runtime)
        finally:
            sub.close()


@attrs.define
class _ReactWhile[RuntimeT: Runtime](Flow[RuntimeT]):
    """Execute child on every change while condition is true.

    Subscribes using the provided ChangeOp and executes the child flow
    each time a change is detected, until the condition becomes false.

    Flow Building Pattern:
        The changed key is available via runtime.attributes as "changed_key".
        Combines reactive and conditional patterns.

    Use cases:
        - Process changes until completion
        - Bounded reactive processing
        - Conditional event handling
    """

    change: ChangeOp = attrs.field()
    condition: Term | bool = attrs.field(default=True)
    child: Flow | Term | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)

    async def run(self, runtime: RuntimeT) -> None:
        """Execute child on each change while condition holds."""
        if not self.child:
            raise ValueError("No child is provided")

        change_event = threading.Event()
        changed_key_holder: dict[str, Key] = {}
        lock = threading.Lock()

        def on_change(changed_key: Key) -> None:
            with lock:
                changed_key_holder["key"] = changed_key
                change_event.set()

        sub = runtime.terms.execute_term(self.change)

        try:
            loop = asyncio.get_running_loop()

            with sub(on_change):
                while True:
                    runtime.cancellation.terminate_cancelled(runtime.path)

                    # Check condition
                    if isinstance(self.condition, Term):
                        condition = runtime.terms.execute_term(self.condition)
                    else:
                        condition = self.condition

                    if not condition:
                        break

                    await loop.run_in_executor(None, change_event.wait, 0.1)

                    if not change_event.is_set():
                        continue

                    with lock:
                        changed_key = changed_key_holder.get("key", ())
                        change_event.clear()

                    runtime.attributes.set(
                        runtime.path,
                        "changed_key",
                        changed_key,
                        step_name=self.name,
                    )

                    await self.execute_child(self.child, 0, runtime)
        finally:
            sub.close()


# =============================================================================
# Wrapper Functions
# =============================================================================


def React(change: ChangeOp, child: Flow | Term | None = None) -> _React:  # noqa: N802
    """Wait for a single change, then execute child.

    Subscribes using the provided ChangeOp and waits for the first change.
    The changed key is available via runtime.attributes as "changed_key".

    Args:
        change: ChangeOp that creates the subscription
        child: Optional child flow to execute after change

    Returns:
        React flow

    Example:
        >>> React(User.status.on_change(), HandleStatusChange())
        >>> React(Config.on_change())  # Just wait, no action
    """
    return _React(change=change, child=child)


def ReactForever(change: ChangeOp, child: Flow | Term, name: str | None = None) -> _ReactForever:  # noqa: N802
    """Execute child on every change (runs forever).

    Subscribes using the provided ChangeOp and executes the child flow
    each time a change is detected. Runs until cancelled.
    The changed key is available via runtime.attributes as "changed_key".

    Args:
        change: ChangeOp that creates the subscription
        child: Child flow to execute on each change
        name: Optional name for attribute tracking

    Returns:
        ReactForever flow

    Example:
        >>> ReactForever(User.tasks.on_children_change(), SyncTask())
        >>> ReactForever(
        ...     Events.on_descendants_change("*", "status"),
        ...     ProcessStatusChange()
        ... )
    """
    return _ReactForever(change=change, child=child, name=name)


def ReactWhile(  # noqa: N802
    change: ChangeOp,
    condition: Term | bool,
    child: Flow | Term,
) -> _ReactWhile:
    """Execute child on every change while condition is true.

    Subscribes using the provided ChangeOp and executes the child flow
    each time a change is detected, until the condition becomes false.
    The changed key is available via runtime.attributes as "changed_key".

    Args:
        change: ChangeOp that creates the subscription
        condition: Condition to check before each iteration
        child: Child flow to execute on each change

    Returns:
        ReactWhile flow

    Example:
        >>> ReactWhile(
        ...     Queue.items.on_children_change(),
        ...     Queue.is_active.get(),
        ...     ProcessQueueItem()
        ... )
    """
    return _ReactWhile(change=change, condition=condition, child=child)
