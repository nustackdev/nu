"""Stream flow -- drain-then-follow over ordered collections.

The ``cat file; tail -f`` of everybase. One declaration that handles
batch catch-up, live follow, and the seamless transition between them.

Children: ``[advance_op, change_op, body]``
    advance_op: AdvanceCursorOp (implicitly constructed at init)
    change_op: OnChildrenChangeOp (implicitly constructed at init)
    body: user-provided Flow

All children are static tree nodes. auto_atomic wraps advance_op in a
Snapshot automatically. Stream just orchestrates: execute children,
set context attrs, loop.

Runtime values flow through ctx.attrs, read by body via PrimRefs:
    ``key``: the actual data key (e.g. tx_id)
    ``log_key``: the log index key (for cursor tracking)

Example::

    from everybase.abc import IntRef as Var, StrRef as StrVar

    tx_id = Var("tx_id")

    Stream(
        ledger.txs,
        body=Seq(
            If(s.synced_txs[tx_id].missing(),
                process_tx(tx_id),
            ),
            s.cursor.store(StrVar("tx_log_key")),  # persistent cursor
        ),
        key="tx_id",
        log_key="tx_log_key",
    )
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from everybase import Flow, Sentinel
from everybase.abc import ensure_term

from ..morphisms.cursor import AdvanceCursorOp
from ..morphisms.reactive import OnChildrenChangeOp


if TYPE_CHECKING:
    from everybase import Context, Executable


__all__ = [
    "Stream",
]


class Stream(Flow):
    """Drain-then-follow over an ordered collection.

    Iterates existing items (drain), then subscribes and follows new
    items (react). Transition is seamless -- cursor tracks position.

    Children layout: ``[advance_op, change_op, body]``

    All substrate work is in the children (AdvanceCursorOp for reads,
    OnChildrenChangeOp for subscriptions). Stream is pure orchestration:
    execute children, set attrs, loop.

    Args:
        source: Ref/Term resolving to an ordered collection with
                next_key_after() and on_children_change().
        body: Flow executed for each item. Reads current key from
              ctx.attrs via PrimRef.
        key: Attr name for current data key (default: "stream_key").
        log_key: Attr name for current log key (default: "stream_log_key").
        cursor: Ref/Term resolving to initial cursor value for resume.
                If not provided, starts from the beginning.
    """

    def __init__(
        self,
        source: object,
        body: Executable,
        *,
        key: str = "stream_key",
        log_key: str = "stream_log_key",
        cursor: object | None = None,
    ) -> None:
        self._key_attr = key
        self._log_key_attr = log_key

        source_term = ensure_term(source)

        # Cursor ref: PrimRef that reads from ctx.attrs (set by this flow each iteration)
        from everybase.abc import StrRef as StrPrimRef

        cursor_ref = StrPrimRef(log_key)

        # Implicit children -- static tree nodes, visible to deformations
        advance = AdvanceCursorOp(source_term, cursor_ref)
        change = OnChildrenChangeOp(source_term)

        # children: [advance, change, body]
        super().__init__(advance, change, body)

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        # Initialize cursor attrs if not already set (first run, no resume)
        if self._log_key_attr not in ctx.attrs:
            ctx.attrs[self._log_key_attr] = Sentinel()
        if self._key_attr not in ctx.attrs:
            ctx.attrs[self._key_attr] = Sentinel()

        # -- DRAIN PHASE --
        await self._drain(ctx)

        # -- REACT PHASE --
        await self._react(ctx)

    async def _drain(self, ctx: Context) -> None:
        """Drain existing items from source."""
        while True:
            result = await self.children[0].execute(ctx)  # advance_op
            if result is None:
                break
            log_key, actual_key = result
            ctx.attrs[self._key_attr] = actual_key
            ctx.attrs[self._log_key_attr] = log_key
            await self.children[2].execute(ctx)  # body

    async def _react(self, ctx: Context) -> None:
        """Follow new items via reactive subscription."""
        loop = asyncio.get_running_loop()
        event = asyncio.Event()

        def on_change(_changed_key: object) -> None:
            loop.call_soon_threadsafe(event.set)

        sub = await self.children[1].execute(ctx)  # change_op
        sub.bind(on_change)
        try:
            while True:
                await event.wait()
                event.clear()
                await self._drain(ctx)  # drain new items since last cursor
        finally:
            sub.unbind(on_change)
            sub.close()
