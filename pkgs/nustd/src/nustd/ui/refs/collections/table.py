"""``TableRef`` -- a content table: rows and columns of places, any content in each.

The plain table of a page: a spec sheet, a comparison, a legend, a key with a
badge and a link per row. Every cell is a place that holds one child of any
kind, a text, a badge, a row of buttons, a whole card, another table. Rows and
cells are positions, so ``t[r, c]`` is "row r, column c" and the browser draws
them in number order whatever order they were written in.

For rows that are data (sorting, selecting, editing, live row ops, a kv store
behind it) use ``DataTableRef`` instead: its rows are values, not places.

    t = ui.TableRef("specs", parent_ref=page, props={"header": ["Part", "Status"]})
    t[0, 0].to(ui.TextRef).set("Pump")
    t[0, 1].to(ui.BadgeRef).set("ok", "ok")
    t[1, 0].to(ui.TextRef).set("Valve")
    t[1, 1].to(ui.RowRef.slot(gap=2))[0].to(ui.ButtonRef).set("Open")

A default kind for every cell, so the ``.to`` can go:

    t = ui.TableRef("specs", parent_ref=page, item=ui.TextRef)
    t[0, 0].set("Pump")

The header row is ``header=`` labels, and ``t.header[c]`` puts content in a
header cell instead (a label with an icon, a sort control of your own).

- ``t[r, c]``: the cell at row ``r``, column ``c``, both ints >= 0 or int
  terms. Its kind comes from ``item=`` when the table has one; otherwise it
  is a bare place, named with ``.to(Kind)`` before anything is written.
- ``t[r]`` / ``t.row(r)``: the row itself (``TableRowRef``), to erase or hide a
  whole row, or to reach its cells with ``row[c]``.
- ``t.header[c]``: a header cell; ``t.header`` is the header row.
- ``spans``: ``{(r, c): cols}`` or ``{(r, c): (cols, rows)}`` makes the cell at
  ``(r, c)`` cover more than one column or row; the cells it covers are not
  drawn. Header cells span columns with the ``("header", c)`` key.

Only ints address a content table: a row or column has no name of its own,
so ``t["a", 0]``, ``t[-1, 0]`` and ``t[True, 0]`` fail loud.

Same ``[r, c]`` as a placed ``GridRef``, different wire: the table has a row
level (``t[r]`` is a ``TableRowRef`` and cell ``c`` sits under it, so a whole
row erases or hides at once), while the grid places a cell at one segment
``"r,c"`` right under itself and has no rows. Both key spans ``"r,c"``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import ItemRef, Ref, Write, as_spec, check_key, child_at
from nustd.ui.core.places import SetSpan, Span, normalize_spans, place_of, span_key

from .base import CollectionRef


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from nu.domains.shape import Slot
    from nu.lang import Nu
    from nu.lang.args import IntArg, ListArg, StrArg
    from nustd.ui.core import Section


__all__ = ["HEADER", "TableRef", "TableRowRef"]


TableVariant = Literal["default", "borderless", "striped"]
TableDensity = Literal["compact", "default", "comfortable"]
ColumnAlign = Literal["left", "center", "right"]

#: The segment the header row sits at. Body rows are digits, so it never collides.
HEADER = "header"

_ALIGNS = ("left", "center", "right")


def _position(owner: str, key: object) -> object:
    """``key`` as a row or column position: an int >= 0 or an int term; else fail loud."""
    return check_key(owner, key, names=False)


def _span_key(at: object) -> str:
    """A spans key as the wire carries it: ``"r,c"``, the header row as ``"header,c"``."""
    return span_key("TableRef", at, header=HEADER)


def _normalize_align(align: Sequence[str] | None) -> list[str]:
    out = [str(a) for a in align or ()]
    for a in out:
        if a not in _ALIGNS:
            msg = f"column align is one of {', '.join(_ALIGNS)}, not {a!r}"
            raise ValueError(msg)
    return out


class TableRowRef(CollectionRef):
    """One row of a content table, body or header. ``row[c]`` is the cell at column ``c``.

    Built by the table (``t[r]``, ``t.row(r)``, ``t.header``), never on its
    own. It draws nothing by itself: the table lays its cells out.
    """

    _wire_type = "TableRow"

    def __getitem__(self, col: object) -> ItemRef:
        _position(self._table_name(), col)
        return child_at(self, col, self._payload.get("cell"))

    def cell(self, col: IntArg) -> ItemRef:
        """The cell at column ``col``, the same as ``row[col]``."""
        return self[col]

    def _table_name(self) -> str:
        parent = self._parent
        return type(parent).__name__ if parent is not None else "TableRef"


class TableRef(CollectionRef):
    """A content table: cells are places, ``t[r, c]``, any kind in each. Pin chrome on slot().

    `header` is the header row's labels, `align` each column's alignment
    ("left", "center", "right"), `variant` "default" (framed), "borderless"
    or "striped", `density` "compact", "default" or "comfortable" (row
    heights 24 / 28 / 32), `label` the accessible name, `spans` cells that
    cover more than one column or row. `item` is every cell's default kind.
    """

    _wire_type = "Table"

    # The cell spec rides the payload (as a GridRef's item does), so it
    # survives a tree rewrite and the rows read it off the table.
    _takes_item: ClassVar[bool] = True

    def __init__(
        self,
        address: object,
        *,
        item: type[Ref] | Slot | None = None,
        section_cls: type[Section] | None = None,
        parent_ref: Ref | None = None,
        owner_shape: type[Section] | None = None,
        props: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(
            address,
            section_cls=section_cls,
            parent_ref=parent_ref,
            owner_shape=owner_shape,
            props=props,
        )
        self._payload["item"] = as_spec("TableRef", item)

    @classmethod
    def slot(
        cls,
        item: type[Ref] | Slot | None = None,
        /,
        *,
        header: Sequence[str] | None = None,
        align: Sequence[ColumnAlign] | None = None,
        variant: TableVariant = "default",
        density: TableDensity = "default",
        label: str = "Table",
        spans: Mapping[tuple[object, int], Span] | None = None,
    ) -> Self:
        declared = super().slot(
            header=[str(h) for h in header or ()],
            align=_normalize_align(align),
            variant=variant,
            density=density,
            label=label,
            spans=normalize_spans(spans, _span_key),
        )
        if item is not None:
            declared.kwargs["item"] = as_spec("TableRef", item)  # type: ignore[attr-defined]
        return declared

    # --- descent -------------------------------------------------------------

    def __getitem__(self, at: object) -> ItemRef:
        """``t[r, c]`` is a cell; ``t[r]`` is the row."""
        if isinstance(at, tuple):
            if len(at) != 2:
                msg = f"TableRef cells are t[row, column], not t[{at!r}]"
                raise TypeError(msg)
            row, col = at
            return self.row(row)[col]
        return self.row(at)  # type: ignore[return-value]

    def row(self, r: IntArg) -> TableRowRef:
        """The body row at position ``r``."""
        _position(type(self).__name__, r)
        return self._row_at(r)

    def cell(self, r: IntArg, c: IntArg) -> ItemRef:
        """The cell at row ``r``, column ``c``, the same as ``t[r, c]``."""
        return self[r, c]

    @property
    def header(self) -> TableRowRef:
        """The header row; ``t.header[c]`` puts content in header cell ``c``."""
        return self._row_at(HEADER)

    def _row_at(self, key: object) -> TableRowRef:
        row = TableRowRef(key, parent_ref=self)
        row._payload["cell"] = self._payload.get("item")
        return row

    # --- chrome --------------------------------------------------------------

    def set_header(self, labels: ListArg[str]) -> Nu:
        """Replace the header labels; header cells with content keep it."""
        return Write(self, Dict.of(header=labels))

    def set_align(self, align: ListArg[str]) -> Nu:
        """Replace every column's alignment, "left", "center" or "right" by position."""
        value = _normalize_align(align) if isinstance(align, list) else align
        return Write(self, Dict.of(align=value))

    def set_span(self, cell: tuple[IntArg | StrArg, IntArg], cols: IntArg, rows: IntArg = 1) -> Nu:
        """Span one cell, leaving the others as they are; 1 by 1 makes it plain again.

        ``cell`` is ``(row, column)``, the way ``spans=`` keys it; ``row`` is a
        body row position, or ``"header"`` for a header cell.
        """
        key = place_of(type(self).__name__, cell, what="a table cell", header=HEADER)
        # The same op as a Grid cell span: one entry of the spans map, keyed "r,c".
        return SetSpan(self, key, cols, rows)
