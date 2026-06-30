"""Interactions for JQueueRef / JQueueForm.

- Put   — Command, blocks when full → back-pressure.
- Get   — ScalarQuery, blocks when empty, yields one item.
- QSize — ScalarQuery, snapshot count.
- Close — Command, shuts down both halves.

TODO(nu-model): Get is a *mutating* Query. The current Query/Command
split forbids WRITE in Query own_effects, so Get does not declare WRITE
on slot 0 — its mutation of the underlying janus.Queue is invisible to
the effect tracker. Acceptable for now; revisit when a dedicated
Interaction kind for queue-style consume-and-return is introduced.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

import janus

from nu.terms.command import ScalarCommand
from nu.terms.query import ScalarQuery
from nu.terms.types import Effect, Mode


if TYPE_CHECKING:
    from .form import JQueueForm


__all__ = [
    "Close",
    "Get",
    "Put",
    "QSize",
    "QueueClosed",
]


_BOTH = frozenset({Mode.SYNC, Mode.ASYNC})

_SHUTDOWN_EXCS: tuple[type[BaseException], ...] = (
    janus.ShutDown,
    janus.SyncQueueShutDown,
    janus.AsyncQueueShutDown,
    janus.QueueShutDown,
)


class QueueClosed(Exception):  # noqa: N818
    """Raised by Get when shut down and empty, or by Put when shut down."""


def _normalize_shutdown(exc: BaseException) -> QueueClosed:
    return QueueClosed(str(exc) or "queue is closed")


class Put(ScalarCommand):
    """Put a value into a JQueueRef. Blocks when full → back-pressure.

    Children: ``[queue, value]``.
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, queue: JQueueForm, value: Any) -> None:  # noqa: ANN401
        super().__init__(queue, value)

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        q = runtime.first(self._children[0], ctx)
        value = runtime.first(self._children[1], ctx)
        try:
            q.sync_q.put(value)
        except _SHUTDOWN_EXCS as e:
            raise _normalize_shutdown(e) from e

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        q = await runtime.afirst(self._children[0], ctx)
        value = await runtime.afirst(self._children[1], ctx)
        try:
            await q.async_q.put(value)
        except _SHUTDOWN_EXCS as e:
            raise _normalize_shutdown(e) from e


class Get(ScalarQuery):
    """Pop one value from a JQueueRef. Blocks when empty.

    Children: ``[queue]``. Yields the popped item.

    NOTE: Mutating Query (gray zone in the current Q/C split). See
    module TODO.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, queue: JQueueForm) -> None:
        super().__init__(queue)

    def eval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        q = self._children[0].eval(ctx)
        try:
            return q.sync_q.get()
        except _SHUTDOWN_EXCS as e:
            raise _normalize_shutdown(e) from e

    async def aeval(self, ctx: Any) -> Any:  # noqa: ANN401, D102
        q = await self._children[0].aeval(ctx)
        try:
            return await q.async_q.get()
        except _SHUTDOWN_EXCS as e:
            raise _normalize_shutdown(e) from e


class QSize(ScalarQuery):
    """Snapshot count of items in a JQueueRef.

    Children: ``[queue]``. Yields an int.
    """

    support: ClassVar[frozenset[Mode]] = _BOTH
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, queue: JQueueForm) -> None:
        super().__init__(queue)

    def eval(self, ctx: Any) -> int:  # noqa: ANN401, D102
        q = self._children[0].eval(ctx)
        return q.sync_q.qsize()

    async def aeval(self, ctx: Any) -> int:  # noqa: ANN401, D102
        q = await self._children[0].aeval(ctx)
        return q.async_q.qsize()


class Close(ScalarCommand):
    """Shut down a JQueueRef.

    Subsequent puts raise; pending and subsequent gets drain remaining
    items, then raise QueueClosed.

    Children: ``[queue]``.
    """

    own_effects: ClassVar[dict[int, Effect]] = {0: Effect.WRITE}
    support: ClassVar[frozenset[Mode]] = _BOTH

    def __init__(self, queue: JQueueForm) -> None:
        super().__init__(queue)

    def run(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        q = runtime.first(self._children[0], ctx)
        q.shutdown()

    async def arun(self, ctx: Any) -> None:  # noqa: ANN401, D102
        from nu import runtime

        q = await runtime.afirst(self._children[0], ctx)
        q.shutdown()
