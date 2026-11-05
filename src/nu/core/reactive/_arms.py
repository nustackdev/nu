"""The arm book: live arms kept by id, for the flows that run one body per id.

A flow that runs a body per id (``ReconcileLatestEach``, ``ReconcileLatest``,
``ReactLatestEach``) keeps an ``ArmBook``: a dict from id to the task running
that id's arm. Ids are whatever the flow keys by, an element read from state
or a notification key, as long as they are hashable. How an arm is started is
the flow's business: the book is handed a ``spawn`` callable that starts one
arm for one id and returns its task.

Two ways to move the live set. ``align(ids)`` makes it match a read: an id
with no arm gets one, an arm whose id is gone is cancelled and drained, every
other arm keeps running untouched. ``restart(id)`` cancels and drains that
one id's arm, if any, and starts it again. ``drain`` cancels and drains all
of them on the way out.

Two rules the book keeps for every flow that holds one:

- An arm runs once per appearance of its id (with ``once``). A finished arm
  is remembered as done and ``align`` does not start it again until its id
  is absent from a read; once the id returns, it may be born again. A flow
  that keys by notification leaves ``once`` off: there a restart is the only
  way an id comes back.
- An arm error ends the flow. The book notices an arm that raised and the
  flow sees the error at its next ``wait`` or ``align``, whichever comes
  first, so an error cuts into a wait for a wake. The flow then drains the
  siblings, closes its subscription and re-raises. Isolation and supervision
  are composed by the user with ``TryCatch`` and ``Retry``.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.core.flows.parallel._scheduling import _settle


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

__all__ = ["ArmBook", "hashable"]


class ArmBook:
    """Live arms keyed by id: births, deaths, restarts, the done set, the first error.

    Args:
        spawn: starts the arm for one id and returns its task.
        once: remember a finished arm's id as done, so ``align`` does not
            start it again until the id has left a read. Off by default.
        owner: the flow's name, for error messages.

    Notes:
        - Ids must be hashable: the book is a dict keyed by them. An id that
          is not raises ``TypeError`` naming the owner.
        - The first arm to raise is kept. ``wait``, ``align`` and ``restart``
          raise it, and nothing is started after it.
        - An arm cancelled by a death or a restart is not done and not an
          error; one that raises something else while it unwinds is an error
          like any other.
        - Built on the flow's event loop and not thread safe: every call
          runs on that loop.
    """

    def __init__(
        self,
        spawn: Callable[[object], asyncio.Task],
        *,
        once: bool = False,
        owner: str = "ArmBook",
    ) -> None:
        self._spawn = spawn
        self._owner = owner
        self.arms: dict[object, asyncio.Task] = {}
        self.done: set[object] | None = set() if once else None
        self._failed: asyncio.Future = asyncio.get_running_loop().create_future()

    @property
    def failed(self) -> bool:
        """Whether an arm has raised."""
        return self._failed.done()

    async def wait(self, aw: Awaitable) -> object:
        """Await ``aw``, unless an arm raises first: then its error is raised here instead.

        The flow waits for its wakes through this, so an arm that raises
        while nothing else is happening still ends the flow at once. When
        the error wins, ``aw`` is cancelled and drained before it is raised;
        when both land on the same tick, the error wins.
        """
        task = asyncio.ensure_future(aw)
        try:
            if not self._failed.done():
                await asyncio.wait({task, self._failed}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            await _settle([task])
        self._raise_failed()
        return task.result()

    def sweep(self) -> None:
        """Take every arm that has already ended off the book.

        A done callback lands a tick late, and an arm that ended should be
        settled on this pass, not the one after it.
        """
        for key, task in [(k, t) for k, t in self.arms.items() if t.done()]:
            self._forget(key, task)

    async def align(self, ids: Iterable) -> None:
        """Make the book hold exactly one live arm per id in ``ids``, under the two rules.

        An id with no arm gets one; an arm whose id is gone is cancelled and
        awaited here rather than left to unwind on its own time, so the id is
        genuinely free by the time this returns and a later birth can never
        overlap the death it followed. Every other arm is untouched, which is
        the point. With ``once``, an id whose arm finished is skipped while
        it stays in the read, and forgotten as done once it is absent.

        Raises:
            TypeError: an id that is not hashable.
            The first arm error, if any arm has raised.
        """
        wanted = _unique(self._owner, ids)
        self.sweep()
        self._raise_failed()
        live = set(wanted)
        for key in [k for k in self.arms if k not in live]:
            # A later death may end on its own while an earlier one drains.
            # Its done callback has then already settled it (off the book,
            # done or the error), so there is nothing left to kill.
            task = self.arms.pop(key, None)
            if task is not None:
                await self._kill(task)
        # A sibling may have raised while a death was drained: nothing is
        # born after an error.
        self._raise_failed()
        if self.done is not None:
            self.done &= live
        for key in wanted:
            if key in self.arms or (self.done is not None and key in self.done):
                continue
            self._birth(key)

    async def restart(self, key: object) -> None:
        """Cancel and drain the arm for ``key``, if one runs, and start it again.

        A restart is a new appearance of the id, so with ``once`` it is also
        born again when its last arm had finished.

        Raises:
            TypeError: an id that is not hashable.
            The first arm error, if any arm has raised.
        """
        _unique(self._owner, (key,))
        self.sweep()
        self._raise_failed()
        task = self.arms.pop(key, None)
        if task is not None:
            await self._kill(task)
            # A sibling may have raised while the stale arm unwound: nothing
            # is born after an error.
            self._raise_failed()
        if self.done is not None:
            self.done.discard(key)
        self._birth(key)

    async def drain(self) -> None:
        """Cancel every live arm and wait until each has fully unwound."""
        tasks = list(self.arms.values())
        self.arms.clear()
        await _settle(tasks)

    def _birth(self, key: object) -> None:
        task = self._spawn(key)
        self.arms[key] = task
        task.add_done_callback(lambda t, k=key: self._forget(k, t))

    async def _kill(self, task: asyncio.Task) -> None:
        """Cancel an arm already taken off the book and drain it; an unwind that raises is an error."""
        await _settle([task])
        if not task.cancelled() and (exc := task.exception()) is not None:
            self._fail(exc)
            self._raise_failed()

    def _forget(self, key: object, task: asyncio.Task) -> None:
        """Settle an arm that ended on its own: off the book, into the done set or the error.

        Runs from the task's done callback and from ``sweep``, whichever is
        first; the second call finds the arm gone and does nothing. An arm
        already taken off the book by a death or a restart is settled there,
        not here.
        """
        if self.arms.get(key) is not task:
            return
        del self.arms[key]
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            self._fail(exc)
        elif self.done is not None:
            self.done.add(key)

    def _fail(self, exc: BaseException) -> None:
        if not self._failed.done():
            self._failed.set_result(exc)

    def _raise_failed(self) -> None:
        if self._failed.done():
            raise self._failed.result()


def hashable(owner: str, key: object) -> None:
    """Check that ``key`` can key a book; a clear error naming ``owner`` when it cannot.

    Shared with the engines that key by notification before they reach the
    book (``KeyedQueues``), so every flow raises the same message.
    """
    try:
        hash(key)
    except TypeError:
        msg = f"{owner}: ids must be hashable, got {type(key).__name__} {key!r}"
        raise TypeError(msg) from None


def _unique(owner: str, ids: Iterable) -> list:
    """``ids`` in order with repeats dropped; a clear error on one that cannot be a key."""
    ids = list(ids)
    try:
        return list(dict.fromkeys(ids))
    except TypeError:
        for key in ids:
            hashable(owner, key)
        raise
