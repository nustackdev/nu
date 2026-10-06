"""Display / output Refs -- server-owned sinks that render into the body.

Server pushes values via `write` / `append`; the browser only renders,
never reads back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.forms import Dict, List
from nu.lang.sentinels import UNSET
from nustd.ui.core import Append, Changed, Ref, Send, Write


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from nu.lang import Nu
    from nu.lang.args import Arg, BoolArg, DictArg, FloatArg, IntArg, ListArg, StrArg


Variant = Literal["neutral", "info", "warn", "ok", "danger"]


class AlertRef(Ref):
    """Display banner ref. `write` carries partial updates; `notify` fires on user dismiss.

    Variant maps to the Alert primitive's `tone` (5 tones per kit): `neutral`
    picks the plain elevated surface, the rest attach the matching status
    wash / line / fg + auto icon. The renderer falls back to `neutral` for
    unmapped values.
    """

    _wire_type = "AlertRef"

    @classmethod
    def slot(
        cls,
        *,
        variant: Variant = "info",
        title: str = "",
        body: str = "",
        dismissible: bool = False,
    ) -> Self:
        return super().slot(variant=variant, title=title, body=body, dismissible=dismissible)

    def set_variant(self, name: Variant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set_body(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(body=text))

    def set_dismissible(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(dismissible=flag))

    def set(
        self,
        title: StrArg,
        body: StrArg = UNSET,
        variant: Variant | StrArg = UNSET,
        dismissible: BoolArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"title": title}
        if body is not UNSET:
            payload["body"] = body
        if variant is not UNSET:
            payload["variant"] = variant
        if dismissible is not UNSET:
            payload["dismissible"] = dismissible
        return Write(self, Dict.of(**payload))

    def on_dismiss(self) -> Changed:
        return Changed(self)


BadgeVariant = Literal["info", "warn", "ok", "danger", "neutral", "dashed"]


class BadgeRef(Ref):
    """Display-only badge ref. One `write` op carries every mutation.

    Variant maps to the Badge primitive's status tones; `neutral` becomes the
    kit `outline` (transparent bg, muted border). `dashed` is the unfilled
    chip for a value that is not there, like "empty" or "none".
    """

    _wire_type = "BadgeRef"

    @classmethod
    def slot(cls, *, label: str = "", variant: BadgeVariant = "neutral") -> Self:
        return super().slot(label=label, variant=variant)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_variant(self, name: BadgeVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set(
        self,
        label: StrArg,
        variant: BadgeVariant | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not UNSET:
            payload["variant"] = variant
        return Write(self, Dict.of(**payload))


Align = Literal["left", "center", "right"]


class DividerRef(Ref):
    """Display-only divider ref. One `write` op carries every mutation."""

    _wire_type = "DividerRef"

    @classmethod
    def slot(cls, *, label: str = "", align: Align = "center") -> Self:
        return super().slot(label=label, align=align)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_align(self, side: Align | StrArg) -> Nu:
        return Write(self, Dict.of(align=side))

    def set(
        self,
        label: StrArg,
        align: Align | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if align is not UNSET:
            payload["align"] = align
        return Write(self, Dict.of(**payload))


EmptySize = Literal["sm", "md"]


class EmptyStateRef(Ref):
    """What a region says while it has nothing to show.

    `label` is the one line that says what is missing, `description` a smaller
    line under it. `sm` fits a sidebar, `md` a page section.
    """

    _wire_type = "EmptyStateRef"

    @classmethod
    def slot(cls, *, label: str = "", description: str = "", size: EmptySize = "md") -> Self:
        return super().slot(label=label, description=description, size=size)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_description(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(description=text))

    def set_size(self, name: EmptySize | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set(
        self,
        label: StrArg,
        description: StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if description is not UNSET:
            payload["description"] = description
        return Write(self, Dict.of(**payload))


GaugeVariant = Literal["neutral", "ok", "warn", "danger"]


class GaugeRef(Ref):
    """Display-only gauge ref. One `write` op carries every mutation.

    Variant is the tone the arc reads with. `neutral` maps to the kit Gauge
    `accent` tone (brand purple); the other three map 1:1 to status tokens.
    """

    _wire_type = "GaugeRef"

    @classmethod
    def slot(
        cls,
        *,
        value: float = 0.0,
        caption: str = "",
        variant: GaugeVariant = "neutral",
    ) -> Self:
        return super().slot(value=value, caption=caption, variant=variant)

    def set_value(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(value=value))

    def set_caption(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(caption=text))

    def set_variant(self, variant: GaugeVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=variant))

    def set(
        self,
        value: FloatArg,
        caption: StrArg = UNSET,
        variant: GaugeVariant | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if caption is not UNSET:
            payload["caption"] = caption
        if variant is not UNSET:
            payload["variant"] = variant
        return Write(self, Dict.of(**payload))


Align = Literal["left", "center", "right"]


class HeadingRef(Ref):
    """Display-only heading ref. One `write` op carries every mutation."""

    _wire_type = "HeadingRef"

    @classmethod
    def slot(cls, *, label: str = "", level: int = 1, align: Align = "left") -> Self:
        return super().slot(label=label, level=level, align=align)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_level(self, n: IntArg) -> Nu:
        return Write(self, Dict.of(level=n))

    def set_align(self, side: Align | StrArg) -> Nu:
        return Write(self, Dict.of(align=side))

    def set(
        self,
        label: StrArg,
        level: IntArg = UNSET,
        align: Align | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if level is not UNSET:
            payload["level"] = level
        if align is not UNSET:
            payload["align"] = align
        return Write(self, Dict.of(**payload))


Fit = Literal["contain", "cover", "fill"]


class ImageRef(Ref):
    """Display-only image ref. One `write` op carries every mutation."""

    _wire_type = "ImageRef"

    @classmethod
    def slot(
        cls,
        *,
        src: str = "",
        alt: str = "",
        fit: Fit = "contain",
        width: int | None = None,
        height: int | None = None,
        rounded: bool = False,
    ) -> Self:
        return super().slot(
            src=src,
            alt=alt,
            fit=fit,
            width=width,
            height=height,
            rounded=rounded,
        )

    def set_src(self, url: StrArg) -> Nu:
        return Write(self, Dict.of(src=url))

    def set_alt(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(alt=text))

    def set_fit(self, mode: Fit | StrArg) -> Nu:
        return Write(self, Dict.of(fit=mode))

    def set_size(
        self,
        width: IntArg | None,
        height: IntArg | None,
    ) -> Nu:
        return Write(self, Dict.of(width=width, height=height))

    def set_rounded(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(rounded=flag))

    def set(
        self,
        src: StrArg,
        alt: StrArg = UNSET,
        fit: Fit | StrArg = UNSET,
        width: IntArg = UNSET,
        height: IntArg = UNSET,
        rounded: BoolArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"src": src}
        if alt is not UNSET:
            payload["alt"] = alt
        if fit is not UNSET:
            payload["fit"] = fit
        if width is not UNSET:
            payload["width"] = width
        if height is not UNSET:
            payload["height"] = height
        if rounded is not UNSET:
            payload["rounded"] = rounded
        return Write(self, Dict.of(**payload))


Theme = Literal["light", "dark"]


class JsonViewerRef(Ref):
    """Display-only json viewer ref. One `write` op carries every mutation via partial-merge."""

    _wire_type = "JsonViewerRef"

    @classmethod
    def slot(
        cls,
        *,
        value: object = None,
        expand_depth: int = 1,
        theme: Theme = "light",
        copyable: bool = False,
        sortable: bool = False,
        max_height: int | None = None,
    ) -> Self:
        return super().slot(
            value=value,
            expand_depth=expand_depth,
            theme=theme,
            copyable=copyable,
            sortable=sortable,
            max_height=max_height,
        )

    def set_value(self, value: Arg[Any]) -> Nu:
        return Write(self, Dict.of(value=value))

    def set_expand_depth(self, depth: IntArg) -> Nu:
        return Write(self, Dict.of(expand_depth=depth))

    def set_theme(self, name: Theme | StrArg) -> Nu:
        return Write(self, Dict.of(theme=name))

    def set_copyable(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(copyable=flag))

    def set_sortable(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(sortable=flag))

    def set_max_height(self, px: IntArg | None) -> Nu:
        return Write(self, Dict.of(max_height=px))

    def set(
        self,
        value: Arg[Any],
        expand_depth: IntArg = UNSET,
        theme: Theme | StrArg = UNSET,
        copyable: BoolArg = UNSET,
        sortable: BoolArg = UNSET,
        max_height: IntArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if expand_depth is not UNSET:
            payload["expand_depth"] = expand_depth
        if theme is not UNSET:
            payload["theme"] = theme
        if copyable is not UNSET:
            payload["copyable"] = copyable
        if sortable is not UNSET:
            payload["sortable"] = sortable
        if max_height is not UNSET:
            payload["max_height"] = max_height
        return Write(self, Dict.of(**payload))


ListVariant = Literal["bullet", "number"]


class ListRef(Ref):
    """A bulleted or numbered list of short text items, display only.

    One string per item, drawn as given. `set` replaces the items whole,
    `append` adds one to the end. `start` is the first number of a numbered
    list. Composes the kit List primitive, which draws a list the way a
    markdown list renders in prose.
    """

    _wire_type = "ListRef"

    @classmethod
    def slot(
        cls,
        *,
        items: list[str] | None = None,
        variant: ListVariant = "bullet",
        start: int = 1,
    ) -> Self:
        return super().slot(items=list(items or []), variant=variant, start=start)

    def set(
        self,
        items: ListArg[str],
        variant: ListVariant | StrArg = UNSET,
        start: IntArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"items": items}
        if variant is not UNSET:
            payload["variant"] = variant
        if start is not UNSET:
            payload["start"] = start
        return Write(self, Dict.of(**payload))

    def set_variant(self, name: ListVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def append(self, item: StrArg) -> Nu:
        return Append(self, item)

    def clear(self) -> Nu:
        return Write(self, Dict.of(items=[]))


Target = Literal["_self", "_blank"]


class LinkRef(Ref):
    """Display-only link ref. One `write` op carries every mutation."""

    _wire_type = "LinkRef"

    @classmethod
    def slot(
        cls,
        *,
        href: str = "",
        label: str = "",
        target: Target = "_self",
        external: bool | None = None,
    ) -> Self:
        return super().slot(href=href, label=label, target=target, external=external)

    def set_href(self, url: StrArg) -> Nu:
        return Write(self, Dict.of(href=url))

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_target(self, name: Target | StrArg) -> Nu:
        return Write(self, Dict.of(target=name))

    def set_external(self, flag: BoolArg | None) -> Nu:
        return Write(self, Dict.of(external=flag))

    def set(
        self,
        href: StrArg = UNSET,
        label: StrArg = UNSET,
        target: Target | StrArg = UNSET,
        external: BoolArg | None = UNSET,
    ) -> Nu:
        # Sentinel-based kwargs so callers can pass `external=None` (auto)
        # without conflating it with "do not touch this field".
        payload: dict[str, object] = {}
        if href is not UNSET:
            payload["href"] = href
        if label is not UNSET:
            payload["label"] = label
        if target is not UNSET:
            payload["target"] = target
        if external is not UNSET:
            payload["external"] = external
        return Write(self, Dict.of(**payload))


class ProgressRef(Ref):
    """Display-only progress ref. One `write` op carries every mutation."""

    _wire_type = "ProgressRef"

    @classmethod
    def slot(
        cls,
        *,
        value: float = 0.0,
        caption: str = "",
        indeterminate: bool = False,
    ) -> Self:
        return super().slot(value=value, caption=caption, indeterminate=indeterminate)

    def set_value(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(value=value))

    def set_caption(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(caption=text))

    def set_indeterminate(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(indeterminate=flag))

    def set(
        self,
        value: FloatArg,
        caption: StrArg = UNSET,
        indeterminate: BoolArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if caption is not UNSET:
            payload["caption"] = caption
        if indeterminate is not UNSET:
            payload["indeterminate"] = indeterminate
        return Write(self, Dict.of(**payload))


Trend = Literal["up", "down", "flat"]


class StatRef(Ref):
    """Display-only stat ref. Server-owned, single `write` op carries partial updates."""

    _wire_type = "StatRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        value: str = "",
        delta: str = "",
        trend: Trend = "flat",
    ) -> Self:
        return super().slot(label=label, value=value, delta=delta, trend=trend)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_value(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(value=text))

    def set_delta(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(delta=text))

    def set_trend(self, name: Trend | StrArg) -> Nu:
        return Write(self, Dict.of(trend=name))

    def set(
        self,
        value: StrArg,
        label: StrArg = UNSET,
        delta: StrArg = UNSET,
        trend: Trend | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if label is not UNSET:
            payload["label"] = label
        if delta is not UNSET:
            payload["delta"] = delta
        if trend is not UNSET:
            payload["trend"] = trend
        return Write(self, Dict.of(**payload))


Tone = Literal["neutral", "info", "ok", "warn", "danger"]


class StatusDotRef(Ref):
    """A tone dot for a live state (connected, running, failing).

    A dot is color only, so give it a `label` unless text next to it already
    says the state: the label is what a screen reader announces. `pulse`
    animates it, for a state still in motion.
    """

    _wire_type = "StatusDotRef"

    @classmethod
    def slot(cls, *, tone: Tone = "neutral", label: str = "", pulse: bool = False) -> Self:
        return super().slot(tone=tone, label=label, pulse=pulse)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_pulse(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(pulse=flag))

    def set(
        self,
        tone: Tone | StrArg,
        label: StrArg = UNSET,
        pulse: BoolArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"tone": tone}
        if label is not UNSET:
            payload["label"] = label
        if pulse is not UNSET:
            payload["pulse"] = pulse
        return Write(self, Dict.of(**payload))


KbdVariant = Literal["default", "ghost"]
KbdSize = Literal["sm", "md"]


class KbdRef(Ref):
    """One key cap, display only: a `K`, a `⌘`, an `Esc`.

    Draws its label as given, on any platform. For a combination that should
    read right on every platform (command on a Mac, control elsewhere), use
    `ShortcutRef`. `default` sits on a well, for a hint on its own; `ghost`
    drops it, for a hint inside something that already has a box.
    """

    _wire_type = "KbdRef"

    @classmethod
    def slot(
        cls, *, label: str = "", variant: KbdVariant = "default", size: KbdSize = "md"
    ) -> Self:
        return super().slot(label=label, variant=variant, size=size)

    def set_variant(self, name: KbdVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set_size(self, name: KbdSize | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set(
        self,
        label: StrArg,
        variant: KbdVariant | StrArg = UNSET,
        size: KbdSize | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not UNSET:
            payload["variant"] = variant
        if size is not UNSET:
            payload["size"] = size
        return Write(self, Dict.of(**payload))


class ShortcutRef(Ref):
    """A key combination by key name, display only: `["mod", "K"]`.

    The browser spells it for the reader's platform, one cap per key: `mod`
    is command on a Mac and control elsewhere, and `shift`, `alt`, `enter`,
    `esc`, `tab`, `backspace`, `delete`, `space` and the arrows (`up`,
    `down`, `left`, `right`) get their glyphs. Any other name is the key as
    typed. Modifiers first, in the order they are held.
    """

    _wire_type = "ShortcutRef"

    @classmethod
    def slot(
        cls,
        *,
        keys: list[str] | None = None,
        variant: KbdVariant = "default",
        size: KbdSize = "md",
    ) -> Self:
        return super().slot(keys=list(keys or []), variant=variant, size=size)

    def set_variant(self, name: KbdVariant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set_size(self, name: KbdSize | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set(
        self,
        keys: ListArg[str],
        variant: KbdVariant | StrArg = UNSET,
        size: KbdSize | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"keys": keys}
        if variant is not UNSET:
            payload["variant"] = variant
        if size is not UNSET:
            payload["size"] = size
        return Write(self, Dict.of(**payload))


SortDirection = Literal["asc", "desc"]
Selection = Literal["none", "single", "multi"]

# ---- table interactions -----------------------------------------------------
#
# A table's own changes, each its own op on the wire (``set_row``,
# ``insert_row``, ``remove_rows``, ``set_order``) and its own handler on the
# browser's TableRef node. The TableRef methods build them; they are exported
# for code that composes frames directly. Keys are the ones the browser draws:
# the ``row_key`` field, or the position as a string without one.


class SetRow(Send):
    """Replace the row keyed ``key`` with ``row``, or add it last when none is shown."""

    _payload_fields = ("key", "row")


class InsertRow(Send):
    """Insert ``row`` before the row at ``index``, clamped to the rows shown."""

    _payload_fields = ("index", "row")


class RemoveRows(Send):
    """Drop the rows with these ``keys``; keys not shown are skipped."""

    _payload_fields = ("keys",)


class SetOrder(Send):
    """Show the rows named by ``keys`` first, in that order; the rest keep theirs after."""

    _payload_fields = ("keys",)


class TableRef(Ref):
    """Rows and columns. The server owns the rows; the browser reports what you do.

    Reads by default: a header click asks for a sort, and that is all. Each
    flag below turns on one more thing to ask for. Everything the user does
    arrives as one notify on the table, its kind named in the payload's
    ``event`` field, and each ``on_*`` takes only its own kind::

        class Shelf(nustd.ui.Page):
            table = nustd.ui.TableRef.slot(
                columns=["id", {"key": "title", "label": "Title"}],
                row_key="id",
                editable=True,
            )

        nu.ReactForever(Shelf.table.on_edit(), lambda ev: save(ev["key"], ev["column"], ev["value"]))

    The browser never changes the rows itself. An edit, an add, a delete or a
    move is a request: the server applies it to whatever the table stands for
    and ships the rows again, all of them with :meth:`set_rows` or only what
    changed with :meth:`set_row`, :meth:`insert_row`, :meth:`remove_rows` and
    :meth:`set_order` (a sort it confirms with :meth:`set_sort`). A request
    the server turns down leaves the table as it was. Which rows are selected
    the browser keeps as you click, and the server can set it with
    :meth:`set_selected`.

    **Column requests** (``columns_editable``) work the same way: an insert,
    delete, rename, move, kind or align change arrives as an ``on_column_*``
    event, and the server confirms it by shipping the columns again with
    :meth:`set_columns`, and the rows too when it rewrote cells. List rows
    hold cells by position, so a server that inserts, deletes or moves
    columns must ship list rows again with their cells where the new columns
    are, in one frame with the columns: ``table.set({"columns": ..., "rows":
    ...})``, not ``set_columns(...) | set_rows(...)``, which arrives as two
    frames and shows cells under the wrong header in between. Mapping rows
    hold cells by column key and come through a reshape untouched (a column
    added shows empty until its cells are written). A table always keeps one
    column: delete is not offered on the last one::

        nu.ReactForever(
            Shelf.table.on_column_rename(),
            lambda ev: Shelf.table.set_columns(renamed(ev["column"], ev["label"])),
        )

    **Columns** are strings or mappings, mixed freely. A string ``s`` is
    ``{"key": s}``; a mapping is ``{key, label?, kind?, options?, editable?,
    align?, width?, sortable?}`` with ``kind`` one of "text" (the default),
    "number", "bool" or "select" (picks from ``options``). Every column sorts
    unless it says ``sortable: False``.

    **Rows** are lists (cells by column position) or mappings (cells by column
    key), mixed freely. ``row_key`` names the field that keys a row: a column
    key for list rows, any field for mapping rows.

    **Row keys.** Without ``row_key`` a row's key is its position as a string,
    and the selection the browser keeps follows positions, not rows; so set
    ``row_key`` whenever rows can be inserted, deleted, moved or re-sorted. Its
    values must be unique: a duplicate gets "~2", "~3", ... in order so the
    grid still works, and that suffixed key is what events carry. A row whose
    key is missing or empty falls back to its index, which may collide with a
    real key, so give every row one. Every event that names rows by key also
    names them by position (``row_index``, ``row_indexes``), so a table
    without ``row_key`` is still fully usable. Keys of rows that are no longer
    shown drop out of the selection.

    **Positions** (``row_index``, ``row_indexes``, the add and move ``index``)
    count within the rows shown, which under ``max_rows`` are the newest ones.

    Args:
        columns: The columns, strings or mappings (see above).
        label: The table's accessible name, eg "Movies".
        striped: Alternate rows tinted.
        dense: The compact row height.
        max_rows: Keep only the newest rows on ``set``, ``append``, ``set_row``
            and ``insert_row``; 0 keeps all.
        sort_column: The column the arrows show, by key.
        sort_direction: "asc" or "desc".
        clickable_rows: A row click arrives on :meth:`on_row_click`.
        row_key: The field that keys a row (see above).
        selection: "single" or "multi" rows select; the selection arrives on
            :meth:`on_select`.
        editable: Cells edit in place, every column but ``row_key`` and those
            that say ``editable: False``; an edit arrives on :meth:`on_edit`.
        addable: An "Add row" button and insert above / below in the row
            menu; a request arrives on :meth:`on_add`.
        deletable: Delete or the row menu; a request arrives on :meth:`on_delete`.
        draggable: Rows move by Alt + Up / Down, the row menu or a drag; a
            request arrives on :meth:`on_move`.
        columns_editable: Columns can be inserted, deleted, renamed, moved,
            and given another kind or alignment, from the column handle's
            menu, a header right-click or F2 on a header; each request
            arrives on its ``on_column_*``.
    """

    _wire_type = "TableRef"

    @classmethod
    def slot(
        cls,
        *,
        columns: Sequence[str | Mapping[str, object]] | None = None,
        label: str = "Table",
        striped: bool = True,
        dense: bool = False,
        max_rows: int = 0,
        sort_column: str = "",
        sort_direction: SortDirection = "asc",
        clickable_rows: bool = False,
        row_key: str = "",
        selection: Selection = "none",
        editable: bool = False,
        addable: bool = False,
        deletable: bool = False,
        draggable: bool = False,
        columns_editable: bool = False,
    ) -> Self:
        return super().slot(
            columns=[c if isinstance(c, str) else dict(c) for c in columns or ()],
            label=label,
            striped=striped,
            dense=dense,
            max_rows=max_rows,
            sort_column=sort_column,
            sort_direction=sort_direction,
            clickable_rows=clickable_rows,
            row_key=row_key,
            selection=selection,
            editable=editable,
            addable=addable,
            deletable=deletable,
            draggable=draggable,
            columns_editable=columns_editable,
        )

    # --- server -> browser ---------------------------------------------------

    def set(self, table: DictArg[str, Any]) -> Nu:
        """Merge any props, eg ``{"columns": [...], "rows": [...]}``."""
        return Write(self, table)

    def set_rows(self, rows: ListArg[Any]) -> Nu:
        """Replace every row. The selection stays where its keys still apply."""
        return Write(self, Dict.of(rows=rows))

    def clear(self) -> Nu:
        """Drop every row."""
        return Write(self, Dict.of(rows=[]))

    def append(self, row: ListArg[Any] | DictArg[str, Any]) -> Nu:
        """Add one row at the end, a list or a mapping; ``max_rows`` drops the oldest."""
        return Append(self, row)

    def set_columns(self, columns: ListArg[Any]) -> Nu:
        """Replace the columns, strings or mappings as on the slot; the rows stay.

        Mapping rows follow the columns by key. Over list rows a reshape
        (insert, delete, move) needs the rows in the same frame:
        ``set({"columns": columns, "rows": rows})``, since a second frame
        would show the old cells under the new headers until it lands.
        """
        return Write(self, Dict.of(columns=columns))

    # The row-level ops below each ship one frame of their own (``SetRow``,
    # ``InsertRow``, ``RemoveRows``, ``SetOrder``) with only the row or the
    # order that changed. They name rows by key as the browser computes
    # it (the ``row_key`` field, or the position as a string without one), and
    # the first row with that key is the one they touch.

    def set_row(self, key: StrArg, row: ListArg[Any] | DictArg[str, Any]) -> Nu:
        """Replace the row keyed ``key`` in place, or add it at the end if none is shown.

        An upsert: a row that is new to the browser lands last (``max_rows``
        drops the oldest), and :meth:`set_order` can put it where it belongs.
        ``row`` is a whole row, a list or a mapping, not a partial one.
        """
        return SetRow(self, key, row)

    def insert_row(self, index: IntArg, row: ListArg[Any] | DictArg[str, Any]) -> Nu:
        """Insert ``row`` before the row at ``index``, or last past the end.

        ``index`` counts the rows shown and is clamped to them; ``max_rows``
        then drops the oldest.
        """
        return InsertRow(self, index, row)

    def remove_row(self, key: StrArg) -> Nu:
        """Drop the row keyed ``key``; a key not shown is a no-op."""
        return RemoveRows(self, List.of(key))

    def remove_rows(self, keys: ListArg[str]) -> Nu:
        """Drop the rows with these keys; keys not shown are skipped."""
        return RemoveRows(self, keys)

    def set_order(self, keys: ListArg[str]) -> Nu:
        """Reorder the rows shown to these keys, without shipping a row.

        Rows named come first in this order; the ones left out keep their
        order after them; keys not shown are skipped.
        """
        return SetOrder(self, keys)

    def set_sort(self, column: StrArg, direction: SortDirection | StrArg) -> Nu:
        """Show the arrows on ``column``; the rows are the server's to sort."""
        return Write(self, Dict.of(sort_column=column, sort_direction=direction))

    def set_selected(self, keys: ListArg[str]) -> Nu:
        """Select exactly these rows, by key; [] selects none."""
        return Write(self, Dict.of(selected=keys))

    # --- browser -> server ---------------------------------------------------

    def on_change(self) -> Changed:
        """Every event below, each naming itself in ``event``."""
        return Changed(self)

    def on_sort(self) -> Changed:
        """``{event, sort_column, sort_direction}``: a header clicked; confirm with ``set_sort``."""
        return Changed(self, "sort")

    def on_row_click(self) -> Changed:
        """``{event, row_index, key}``: a body row clicked. Needs ``clickable_rows``."""
        return Changed(self, "row")

    def on_select(self) -> Changed:
        """``{event, keys, row_indexes}``: the whole next selection. Needs ``selection``.

        ``row_indexes`` runs parallel to ``keys``: each row's position as shown.
        """
        return Changed(self, "select")

    def on_edit(self) -> Changed:
        """``{event, key, row_index, column, value, previous}``: a cell's new value. Needs ``editable``.

        ``value`` is typed by the column's kind: a str for "text" and
        "select", a number for "number", a bool for "bool".
        """
        return Changed(self, "edit")

    def on_add(self) -> Changed:
        """``{event, index}``: a new row asked for at ``index``. Needs ``addable``.

        The server decides what is in it, and its key.
        """
        return Changed(self, "add")

    def on_delete(self) -> Changed:
        """``{event, keys, row_indexes}``: these rows asked to go. Needs ``deletable``.

        ``row_indexes`` runs parallel to ``keys``: each row's position as shown.
        """
        return Changed(self, "delete")

    def on_move(self) -> Changed:
        """``{event, key, row_index, index}``: a row asked to move. Needs ``draggable``.

        ``row_index`` is where the row is now; ``index`` counts the rows
        without it, so the row lands before the row at that index, or last.
        """
        return Changed(self, "move")

    # Each column event names the column by its key as sent (``column``) and
    # by its position among the columns shown (``column_index``).

    def on_column_add(self) -> Changed:
        """``{event, index}``: a new column asked for at ``index``. Needs ``columns_editable``.

        The server decides what it is (key, label, kind) and confirms with
        :meth:`set_columns`; list rows go again with a cell at ``index``.
        """
        return Changed(self, "column_add")

    def on_column_delete(self) -> Changed:
        """``{event, column, column_index}``: a column asked to go. Needs ``columns_editable``.

        Confirm with :meth:`set_columns`; list rows go again without its
        cells, in the same frame (:meth:`set`). A table always keeps one
        column: the browser does not offer delete on the last one.
        """
        return Changed(self, "column_delete")

    def on_column_rename(self) -> Changed:
        """``{event, column, column_index, label, previous}``: new header text. Needs ``columns_editable``.

        ``label`` is as typed, untrimmed and possibly empty; ``previous`` is
        the label shown. The header keeps ``previous`` until the server
        confirms with :meth:`set_columns`.
        """
        return Changed(self, "column_rename")

    def on_column_move(self) -> Changed:
        """``{event, column, column_index, index}``: a column asked to move. Needs ``columns_editable``.

        ``index`` counts the columns without it, so the column lands before
        the column at that index, or last. Confirm with :meth:`set_columns`;
        list rows go again with their cells moved the same way.
        """
        return Changed(self, "column_move")

    def on_column_kind(self) -> Changed:
        """``{event, column, column_index, kind, previous}``: another kind asked for. Needs ``columns_editable``.

        ``kind`` and ``previous`` are "text", "number", "bool" or "select"
        (``previous`` "text" when the column sets none). Confirm with
        :meth:`set_columns`, and the rows when their cells were converted. A
        column switched to "select" needs its ``options`` sent with it.
        """
        return Changed(self, "column_kind")

    def on_column_align(self) -> Changed:
        """``{event, column, column_index, align, previous}``: another alignment. Needs ``columns_editable``.

        ``align`` and ``previous`` are "left", "center" or "right";
        ``previous`` is what the column shows, its kind's default (number
        right, bool center, else left) when it sets none.
        """
        return Changed(self, "column_align")


class TextRef(Ref):
    """Display-only string ref. Body copy."""

    _wire_type = "TextRef"

    @classmethod
    def slot(cls, *, value: str = "") -> Self:
        return super().slot(value=value)

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)


__all__ = [
    "AlertRef",
    "BadgeRef",
    "DividerRef",
    "EmptyStateRef",
    "GaugeRef",
    "HeadingRef",
    "ImageRef",
    "InsertRow",
    "JsonViewerRef",
    "KbdRef",
    "LinkRef",
    "ListRef",
    "ProgressRef",
    "RemoveRows",
    "SetOrder",
    "SetRow",
    "ShortcutRef",
    "StatRef",
    "StatusDotRef",
    "TableRef",
    "TextRef",
]
