"""Cursor ops -- advance cursor over ordered collections.

AdvanceCursorOp: resolve source view + cursor, return next (log_key, key) or None.
Pure operation -- resolves children, calls view method, returns result.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nu import Op, Calculation, Sentinel


if TYPE_CHECKING:
    from nu import Context


__all__ = [
    "AdvanceCursorOp",
]


class AdvanceCursorOp(Calculation, Op[tuple | None]):
    """Read next key after cursor from an ordered view.

    Children: [source, cursor]
        source: Ref resolving to an ordered view with next_key_after()
        cursor: Ref resolving to current cursor position (or Sentinel if fresh start)

    Returns:
        (log_key, actual_key) tuple if next item exists, None if exhausted.
    """

    def __init__(self, source: object, cursor: object) -> None:
        super().__init__(source, cursor)

    async def execute(self, ctx: Context) -> tuple | None:  # noqa: D102
        view = await self.children[0].execute(ctx)
        cursor = await self.children[1].execute(ctx)

        # Sentinel means no cursor yet (fresh start)
        if isinstance(cursor, Sentinel):
            cursor = None

        return view.next_key_after(cursor)

    def __repr__(self) -> str:
        return f"AdvanceCursorOp({self.children[0]!r}, {self.children[1]!r})"
