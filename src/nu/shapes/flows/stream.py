"""Stream flow -- drain-then-follow over ordered collections.

The ``cat file; tail -f`` of everybase. One declaration that handles
batch catch-up, live follow, and the seamless transition between them.

Children: ``[advance_op, change_op, body, key, log_key]``
    advance_op: AdvanceCursorOp (implicitly constructed at init)
    change_op: OnChildrenChangeOp (implicitly constructed at init)
    body: user-provided Flow
    key: StrArg for the data key attr name
    log_key: StrArg for the log key attr name

All children are static tree nodes. auto_atomic wraps advance_op in a
Snapshot automatically. Stream just orchestrates: execute children,
set context attrs, loop.

Runtime values flow through ctx.attrs, read by body via AttrRefs:
    ``key``: the actual data key (e.g. tx_id)
    ``log_key``: the log index key (for cursor tracking)

Example::

    from nu.context.attr_refs import IntAttrRef, StrAttrRef

    tx_id = IntAttrRef("tx_id").get()

    Stream(
        ledger.txs,
        body=Seq(
            If(s.synced_txs[tx_id].missing(),
                process_tx(tx_id),
            ),
            s.cursor.store(StrAttrRef("tx_log_key").get()),
        ),
        key="tx_id",
        log_key="tx_log_key",
    )
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu import Flow, Sentinel
from nu.utils import ensure_nu

from ..ops.cursor import AdvanceCursorOp
from ..ops.reactive import OnChildrenChangeOp


if TYPE_CHECKING:
    from nu import Context, Nu
    from nu.terms import StrArg


__all__ = [
    "Stream",
]


class Stream(Flow):
    """Drain-then-follow over an ordered collection.

    Iterates existing items (drain), then subscribes and follows new
    items (react). Transition is seamless -- cursor tracks position.

    Children layout: ``[advance_op, change_op, body, key, log_key]``

    All substrate work is in the children (AdvanceCursorOp for reads,
    OnChildrenChangeOp for subscriptions). Stream is pure orchestration:
    execute children, set attrs, loop.

    Args:
        source: Ref/Nu resolving to an ordered collection with
                next_key_after() and on_children_change().
        body: Flow executed for each item. Reads current key from
              ctx.attrs via AttrRef.
        key: Attr name for current data key (default: "stream_key").
        log_key: Attr name for current log key (default: "stream_log_key").
        cursor: Ref/Nu resolving to initial cursor value for resume.
                If not provided, starts from the beginning.
    """

    def __init__(
        self,
        source: object,
        body: Nu,
        *,
        key: StrArg = "stream_key",
        log_key: StrArg = "stream_log_key",
        cursor: object | None = None,
    ) -> None:
        """Initialize stream flow.

        Args:
            source: Ordered collection to drain and follow.
            body: Nu run for each item.
            key: ctx.attrs key for the current data key.
            log_key: ctx.attrs key for the current log key.
            cursor: Optional initial cursor value for resume.
        """
        source_term = ensure_nu(source)

        # Cursor ref: AttrRef that reads log_key from ctx.attrs
        from nu.context.attr_refs import AttrRef

        cursor_ref = AttrRef(log_key)

        # Implicit children -- static tree nodes, visible to deformations
        advance = AdvanceCursorOp(source_term, cursor_ref)
        change = OnChildrenChangeOp(source_term)

        # children: [advance, change, body, key, log_key]
        super().__init__(advance, change, body, ensure_nu(key), ensure_nu(log_key))

    async def execute(self, ctx: Context) -> None:  # noqa: D102
        key = await self.children[3].execute(ctx)
        log_key = await self.children[4].execute(ctx)

        # Initialize cursor attrs if not already set (first run, no resume)
        if log_key not in ctx.attrs:
            ctx.attrs[log_key] = Sentinel()
        if key not in ctx.attrs:
            ctx.attrs[key] = Sentinel()

        # -- DRAIN PHASE --
        await self._drain(ctx, key, log_key)

        # -- REACT PHASE --
        await self._react(ctx, key, log_key)

    async def _drain(self, ctx: Context, key: str, log_key: str) -> None:
        """Drain existing items from source."""
        while True:
            result = await self.children[0].execute(ctx)  # advance_op
            if result is None:
                break
            log_k, actual_key = result
            ctx.attrs[key] = actual_key
            ctx.attrs[log_key] = log_k
            await self.children[2].execute(ctx)  # body

    async def _react(self, ctx: Context, key: str, log_key: str) -> None:
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
                await self._drain(ctx, key, log_key)
        finally:
            sub.unbind(on_change)
            sub.close()
