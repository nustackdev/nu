"""``TreeRef`` -- nested rows that fold, with select, open, rename and move.

The server owns the nodes, the browser owns the moment. The nodes are a flat
list the server ships whole; which rows are open and which one is selected
the browser keeps as you click, and the server can set either. Everything
the user does arrives as one notify on the tree, its kind named in the
payload's ``event`` field, and each ``on_*`` takes only its own kind::

    class Files(nustd.ui.Page):
        tree = nustd.ui.TreeRef.slot(label="Files", editable=True, draggable=True)

    nu.ReactForever(Files.tree.on_open(), lambda ev: open_file(ev["key"]))
    nu.ReactForever(Files.tree.on_rename(), lambda ev: rename(ev["key"], ev["title"]))

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

from nu.forms import Dict
from nustd.ui.core import Changed, Ref, Write


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from nu.lang import Nu
    from nu.lang.args import ListArg, StrArg


__all__ = ["TreeRef"]


class TreeRef(Ref):
    """Nested rows that fold. The server owns the nodes; the browser reports what you do.

    Args:
        label: The tree's accessible name, eg "Files".
        nodes: Seed nodes, ``{key, parent, label}`` each (see the module).
        editable: F2 or the row's right-click menu renames it in place; the
            result arrives on :meth:`on_rename`.
        draggable: Rows drag to reorder and nest; a drop arrives on
            :meth:`on_move`.
    """

    _wire_type: ClassVar[str] = "TreeRef"

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
        return Write(self, Dict.of(nodes=nodes))

    def set_selected(self, key: StrArg) -> Nu:
        """Select a row; "" selects none."""
        return Write(self, Dict.of(selected=key))

    def set_expanded(self, keys: ListArg[str]) -> Nu:
        """Open exactly these rows."""
        return Write(self, Dict.of(expanded=keys))

    # --- browser -> server ---------------------------------------------------

    def on_change(self) -> Changed:
        """Every event below, each naming itself in ``event``."""
        return Changed(self)

    def on_select(self) -> Changed:
        """``{event, key}``: a click or Space on a row."""
        return Changed(self, "select")

    def on_open(self) -> Changed:
        """``{event, key}``: Enter or a double click, the row's "do the thing"."""
        return Changed(self, "open")

    def on_toggle(self) -> Changed:
        """``{event, key, open}``: a row folded or unfolded."""
        return Changed(self, "toggle")

    def on_rename(self) -> Changed:
        """``{event, key, title}``: an inline rename, trimmed and changed. Needs ``editable``."""
        return Changed(self, "rename")

    def on_move(self) -> Changed:
        """``{event, key, parent, index}``: a drop. Needs ``draggable``.

        ``parent`` "" is the top level; ``index`` counts the parent's children
        without ``key``.
        """
        return Changed(self, "move")
