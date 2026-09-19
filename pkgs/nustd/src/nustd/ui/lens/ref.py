"""``LensRef`` -- the lens surface as one Ref.

A widget like any other in the kit, and it obeys the kit's two conventions:
``_wire_type`` names the browser component, and a Ref with one semantically
primary value spells it ``set``. The cascade is not a single value -- it is a
cursor and the columns that cursor produced, always together -- so there is
``set_columns`` and no bare ``set``.

By the kit's grouping it is an output Ref: a server-owned sink the browser
renders and the server never reads back. It lives here rather than in
``refs/output.py`` because it comes with two modules of machinery beside it,
and that machinery is not a widget.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Changed, Ref, Write

from .columns import DEFAULT_MAX_ROWS


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import ListArg


__all__ = ["LensRef"]


class LensRef(Ref):
    """A Shape, browsable as cascading columns. The server reads, the browser walks.

    Both directions carry something, and which half owns what is the whole
    design. The **columns** are the value, and the server owns them: it walks a
    Shape, reads the store and ships the whole cascade with ``set_columns``.
    The **cursor** is an event, and the browser owns it: arrows and clicks move
    it locally and it arrives here on ``on_nav`` as the whole new path, already
    resolved, the same way a table's row click arrives as an index. Nothing is
    ever read back off the node, which is why it groups with the sinks rather
    than with the inputs.

    Where the columns are read from never crosses the wire. A cursor is
    relative to the Shape the caller pointed the lens at, and the prefix that
    says where that Shape lives stays in the program (see
    :mod:`nustd.ui.lens.columns`). So a lens anchored at a subtree cannot be
    talked out of it by anything the browser sends.

    The ref holds no state at all. A reload starts at the root and two tabs
    disagree freely; anything on the server that wants to move a cursor ships a
    ``set_columns`` with the cursor it wants.

    Args:
        max_rows: the per-column cap. Rides in mount props so the browser's
            ``n/total`` note agrees with what was actually clipped.
        height: pixels. A column browser scrolls in both directions, so it
            needs a height rather than growing to fit its deepest column.
    """

    _wire_type = "LensRef"

    @classmethod
    def slot(cls, *, max_rows: int = DEFAULT_MAX_ROWS, height: int = 420) -> Self:
        """Mount the surface, telling the browser what one column holds."""
        return super().slot(max_rows=int(max_rows), height=int(height))

    def set_columns(self, cursor: ListArg[str], columns: ListArg[dict]) -> Nu:
        """Replace the cascade: the cursor, and one column per prefix of it.

        Each column is ``{kind, entries, total}``; each entry is
        ``{key, kind, preview, navigable, vtype}``, plus ``text`` and
        ``clipped`` on a leaf column's single row. A full replacement rather
        than a delta, so a browser that missed a frame is never left holding a
        column it cannot be corrected on.
        """
        return Write(self, Dict.of(cursor=cursor, columns=columns))

    def on_nav(self) -> Changed:
        """The whole new cursor, as a list of segments the browser resolved."""
        return Changed(self)
