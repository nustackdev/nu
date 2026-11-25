"""``TreeRef`` -- nested rows that fold, with select, open, rename and move.

The server owns the nodes, the browser owns the moment. The nodes are a flat
list the server ships whole; which rows are open and which one is selected
the browser keeps as you click, and the server can set either and read both
back: the tree itself reads as the selected key, :meth:`TreeRef.expanded` as
the open keys. Everything the user does arrives as one notify on the tree,
its kind named in the payload's ``event`` field, and each ``on_*`` takes only
its own kind (``on_event()`` takes every one)::

    class Files(nustd.ui.Column):
        tree = nustd.ui.TreeRef.slot(label="Files", editable=True, draggable=True)

    nu.ReactEvery(Files.tree.on_open(), lambda ev: open_file(ev["key"]))
    nu.ReactEvery(Files.tree.on_rename(), lambda ev: rename(ev["key"], ev["title"]))

The browser never changes the nodes itself. A rename or a move is a request:
the server applies it to whatever the tree stands for and ships the nodes
again with :meth:`TreeRef.set`. A request the server turns down leaves the
tree as it was.

**A node** is ``{key, parent, label}`` plus, optionally, ``icon`` (a short
string, eg an emoji) and ``badge`` (a short string after the label).
``parent`` is another node's key, or None / "" at the top. Siblings keep the
order they arrive in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self

from nustd.ui.core import Changed, Emits, Readable, Write
from nustd.ui.core.events import MOVE, OPEN, RENAME, SELECT, TOGGLE

from .base import LeafRef


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from nu.lang import Nu
    from nu.lang.args import ListArg, StrArg
    from nustd.ui.core import ReadField


__all__ = ["TreeRef"]


def _keys(raw: object) -> list[str]:
    """Keys off the wire: a list of strings, anything else none."""
    if not isinstance(raw, (list, tuple)):
        return []
    return [str(k) for k in raw if k is not None]


class TreeRef(Readable, Emits, LeafRef):
    """Nested rows that fold. The server owns the nodes; the browser reports what you do.

    Reading the tree gives the selected key, None when no row is selected;
    :meth:`expanded` gives the open keys. A selection moves on ``select``, the
    open rows on ``toggle``.

    Args:
        label: The tree's accessible name, eg "Files".
        nodes: Seed nodes, ``{key, parent, label}`` each (see the module).
        editable: F2 or the row's right-click menu renames it in place; the
            result arrives on :meth:`on_rename`.
        draggable: Rows drag to reorder and nest; a drop arrives on
            :meth:`on_move`.
    """

    _wire_type: ClassVar[str] = "TreeRef"
    _reader_events: ClassVar[dict[str, str]] = {"expanded": TOGGLE}

    @classmethod
    def slot(
        cls,
        *,
        label: str = "Tree",
        nodes: Sequence[Mapping[str, object]] | None = None,
        editable: bool = False,
        draggable: bool = False,
    ) -> Self:
        return super().slot(
            label=label,
            nodes=[dict(n) for n in nodes or ()],
            editable=editable,
            draggable=draggable,
        )

    # --- server -> browser ---------------------------------------------------

    def set(self, nodes: ListArg[dict]) -> Nu:
        """Replace every node. Open rows and the selection stay where they still apply."""
        from nu.forms import Dict

        return Write(self, Dict.of(nodes=nodes))

    def set_selected(self, key: StrArg) -> Nu:
        """Select a row; "" selects none."""
        from nu.forms import Dict

        return Write(self, Dict.of(selected=key))

    def set_expanded(self, keys: ListArg[str]) -> Nu:
        """Open exactly these rows."""
        from nu.forms import Dict

        return Write(self, Dict.of(expanded=keys))

    # --- reads ---------------------------------------------------------------

    def expanded(self) -> ReadField:
        """The open rows' keys, as the browser holds them now."""
        return self._read("expanded")

    def _lift(self, raw: object) -> str | None:
        return str(raw) if raw not in (None, "") else None

    def _lift_field(self, field: str, raw: object) -> object:
        return _keys(raw) if field == "expanded" else raw

    # --- browser -> server ---------------------------------------------------

    def on_select(self) -> Changed:
        """``{event, key}``: a click or Space on a row."""
        return Changed(self, SELECT)

    def on_open(self) -> Changed:
        """``{event, key}``: Enter or a double click, the row's "do the thing"."""
        return Changed(self, OPEN)

    def on_toggle(self) -> Changed:
        """``{event, key, open}``: a row folded or unfolded."""
        return Changed(self, TOGGLE)

    def on_rename(self) -> Changed:
        """``{event, key, title}``: an inline rename, trimmed and changed. Needs ``editable``."""
        return Changed(self, RENAME)

    def on_move(self) -> Changed:
        """``{event, key, parent, index}``: a drop. Needs ``draggable``.

        ``parent`` "" is the top level; ``index`` counts the parent's children
        without ``key``.
        """
        return Changed(self, MOVE)
