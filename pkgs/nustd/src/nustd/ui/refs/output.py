"""Display / output Refs -- server-owned sinks that render into the body.

Server pushes values via `write` / `append`; the browser only renders,
never reads back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Append, Changed, Ref, Write


if TYPE_CHECKING:
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


class TableRef(Ref):
    """Tabular data; display by default, optional sortable headers and row click.

    Composes the kit Table primitive family. `dense=True` maps to the
    primitive's `compact` density; `striped=True` selects the `striped` variant.

    A header click and a row click are two kinds of notify on the one table,
    named in their `event` field; `on_sort` and `on_row_click` each take only
    their own.
    """

    _wire_type = "TableRef"

    @classmethod
    def slot(
        cls,
        *,
        columns: list[str] | None = None,
        striped: bool = True,
        dense: bool = False,
        max_rows: int = 0,
        sort_column: str = "",
        sort_direction: SortDirection = "asc",
        clickable_rows: bool = False,
    ) -> Self:
        return super().slot(
            columns=list(columns or []),
            striped=striped,
            dense=dense,
            max_rows=max_rows,
            sort_column=sort_column,
            sort_direction=sort_direction,
            clickable_rows=clickable_rows,
        )

    def set(self, table: DictArg[str, Any]) -> Nu:
        return Write(self, table)

    def clear(self) -> Nu:
        return Write(self, Dict.of(rows=[]))

    def append(self, row: ListArg[Any]) -> Nu:
        return Append(self, row)

    def set_sort(self, column: StrArg, direction: SortDirection | StrArg) -> Nu:
        return Write(self, Dict.of(sort_column=column, sort_direction=direction))

    def on_row_click(self) -> Changed:
        """``{event, row_index}``: a body row clicked. Needs ``clickable_rows``."""
        return Changed(self, "row")

    def on_sort(self) -> Changed:
        """``{event, sort_column, sort_direction}``: a header clicked; confirm with ``set_sort``."""
        return Changed(self, "sort")


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
    "JsonViewerRef",
    "KbdRef",
    "LinkRef",
    "ListRef",
    "ProgressRef",
    "ShortcutRef",
    "StatRef",
    "StatusDotRef",
    "TableRef",
    "TextRef",
]
