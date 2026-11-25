"""``LensRef`` -- the lens surface as one Ref.

A widget like any other in the kit, and it obeys the kit's two conventions:
``_wire_type`` names the browser component, and a Ref with one semantically
primary value spells it ``set``. The cascade is not a single value -- it is a
cursor and the columns that cursor produced, always together -- so there is
``set_columns`` and no bare ``set``.

By the kit's grouping it is a content leaf with no children: the server
owns the columns, the browser owns the cursor, and the cursor is the one
thing read back. It lives here rather than in ``refs/leaves/output.py``
because it comes with two modules of machinery beside it, and that machinery
is not a widget.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nustd.ui.core import Changes, Write
from nustd.ui.refs.leaves.base import LeafRef

from .columns import DEFAULT_MAX_ROWS


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import ListArg


__all__ = ["LensRef"]


class LensRef(Changes, LeafRef):
    """A Shape, browsable as cascading columns. The server reads, the browser walks.

    Both directions carry something, and which half owns what is the whole
    design. The **columns** are server state: it walks a Shape, reads the
    store and ships the whole cascade with ``set_columns``. The **cursor** is
    the browser's: arrows and clicks move it, and each move arrives on
    ``on_change`` as ``{event: "change", value: cursor}``, the whole new path
    already resolved. Reading the ref is that cursor, a list of segments: the
    one the person last moved to, or the one ``set_columns`` last shipped,
    whichever came later.

    Where the columns are read from never crosses the wire. A cursor is
    relative to the Shape the caller pointed the lens at, and the prefix that
    says where that Shape lives stays in the program (see
    :mod:`nustd.ui.lens.columns`). So a lens anchored at a subtree cannot be
    talked out of it by anything the browser sends.

    The server side holds no state at all. A reload starts at the root and two
    tabs disagree freely; anything on the server that wants to move a cursor
    ships a ``set_columns`` with the cursor it wants.

    Args:
        max_rows: the per-column cap. Rides in init props so the browser's
            ``n/total`` note agrees with what was actually clipped.
        height: pixels. A column browser scrolls in both directions, so it
            needs a height rather than growing to fit its deepest column.
    """

    _wire_type = "LensRef"

    @classmethod
    def slot(cls, *, max_rows: int = DEFAULT_MAX_ROWS, height: int = 420) -> Self:
        """Declare the surface, telling the browser what one column holds."""
        return super().slot(max_rows=int(max_rows), height=int(height))

    def set_columns(self, cursor: ListArg[str], columns: ListArg[dict]) -> Nu:
        """Replace the cascade: the cursor, and one column per prefix of it.

        Each column is ``{kind, entries, total}``; each entry is
        ``{key, kind, preview, navigable, vtype}``, plus ``text`` and
        ``clipped`` on a leaf column's single row. A full replacement rather
        than a delta, so a browser that missed a frame is never left holding a
        column it cannot be corrected on.
        """
        from nu.forms import Dict

        return Write(self, Dict.of(cursor=cursor, columns=columns))

    def _lift(self, raw: object) -> list[str]:
        # The cursor as segments, [] before anything moved it.
        return [str(s) for s in raw] if isinstance(raw, list) else []
