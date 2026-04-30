"""Cursor queries — advance over ordered collections."""

from __future__ import annotations

from typing import Any, ClassVar

from nu.terms.query import ScalarQuery
from nu.terms.types import Mode


__all__ = [
    "AdvanceCursor",
]


_UNSET = object()


class AdvanceCursor(ScalarQuery):
    """Read next key after cursor from an ordered view.

    Children: [source, cursor]
        source: Ref resolving to an ordered view with next_key_after()
        cursor: Ref resolving to current cursor position (or _UNSET on fresh start)

    Returns:
        (log_key, actual_key) tuple if next item exists, None if exhausted.
    """

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})
    accepts_sentinels: ClassVar[bool] = True

    def __init__(self, source: object, cursor: object) -> None:
        super().__init__(source, cursor)

    def _apply(self, ctx: Any, ops: list[Any]) -> tuple | None:  # noqa: ANN401
        view = ops[0]
        cursor = ops[1]
        if cursor is None or cursor is _UNSET:
            cursor = None
        return view.next_key_after(cursor)

    def __repr__(self) -> str:
        return f"AdvanceCursor({self._children[0]!r}, {self._children[1]!r})"
