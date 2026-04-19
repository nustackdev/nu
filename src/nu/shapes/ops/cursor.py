"""Cursor ops - advance cursor over ordered collections.

AdvanceCursorOp: resolve source view + cursor, return next (log_key, key) or None.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu.terms import Sentinel
from nu.terms.op import Query


if TYPE_CHECKING:
    from nu import Context


__all__ = [
    "AdvanceCursorOp",
]


class AdvanceCursorOp(Query[tuple | None]):
    """Read next key after cursor from an ordered view.

    Children: [source, cursor]
        source: Ref resolving to an ordered view with next_key_after()
        cursor: Ref resolving to current cursor position (or Sentinel if fresh start)

    Returns:
        (log_key, actual_key) tuple if next item exists, None if exhausted.

    Uses Query (not NAryOp) because a Sentinel cursor is a valid input signalling
    "fresh start" - NAryOp's sentinel propagation would short-circuit it.
    """

    def __init__(self, source: object, cursor: object) -> None:
        super().__init__(source, cursor)

    async def run(self, ctx: Context) -> tuple | None:
        view = await self.children[0].first(ctx)
        cursor = await self.children[1].first(ctx)

        # Sentinel means no cursor yet (fresh start)
        if isinstance(cursor, Sentinel):
            cursor = None

        return view.next_key_after(cursor)

    def __repr__(self) -> str:
        return f"AdvanceCursorOp({self.children[0]!r}, {self.children[1]!r})"
