"""Loop and lifecycle primitives.

- ``into_loop`` - run a coroutine to completion from sync code (spinning a
  fresh loop if none is running).
- ``safely_closing`` / ``safely_aclosing`` - context managers that call
  ``close`` / ``aclose`` on exit if the iterable has it, no-op otherwise.
  Use to guarantee generator finalization when iterating an iterable whose
  concrete shape (list, generator, range) is unknown - short-circuited
  generators that aren't closed pile up finalizer Tasks on a busy loop and
  pin their frames, a real memory leak in long-running programs.

Thread-pool primitives live on the Runtime, where they can use the Budget's
pool instead of a module-global one.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, TypeVar


if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterable,
        AsyncIterator,
        Awaitable,
        Coroutine,
        Iterable,
        Iterator,
    )


__all__ = ["into_loop", "safely_aclosing", "safely_closing"]


T = TypeVar("T")


def into_loop(coro: Awaitable[T] | Coroutine[object, object, T]) -> T:
    """Run a coroutine to completion from sync code.

    Spins a fresh loop with ``asyncio.run`` when no loop is running. Raises
    if called while a loop is already running - the caller should be using
    ``aeval`` directly in that case.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_as_coro(coro))
    msg = "into_loop called while a loop is running; call aeval, not eval"
    raise RuntimeError(msg)


async def _as_coro(awaitable: Awaitable[T]) -> T:
    """Adapt a bare Awaitable to a Coroutine for ``asyncio.run``."""
    return await awaitable


@contextmanager
def safely_closing(it: Iterable[T]) -> Iterator[Iterable[T]]:
    """Yield ``it``; on exit call ``close()`` if it has one, else no-op.

    Use to wrap iteration when the iterable's concrete type is unknown -
    generators get finalized even on short-circuit (``break``, ``return``,
    exception); lists and ranges pass through unchanged.
    """
    try:
        yield it
    finally:
        close = getattr(it, "close", None)
        if close is not None:
            close()


@asynccontextmanager
async def safely_aclosing(ait: AsyncIterable[T]) -> AsyncIterator[AsyncIterable[T]]:
    """Async sibling of ``safely_closing``: ``aclose`` on exit if present.

    Critical inside async generators that may short-circuit. Without this,
    CPython queues finalizer ``aclose`` Tasks on the running loop, retaining
    frames and Contexts until GC catches up - on a busy loop, an observable
    memory leak.
    """
    try:
        yield ait
    finally:
        aclose = getattr(ait, "aclose", None)
        if aclose is not None:
            await aclose()
