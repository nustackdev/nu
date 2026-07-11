"""Display / output Refs -- server-owned sinks that render into the body.

Server pushes values via `write` / `append`; the browser only renders,
never reads back. See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from nu import DictForm
from nu.lang.args import Arg, BoolArg, DictArg, FloatArg, IntArg, ListArg, StrArg
from nu.lang.sentinels import UNSET

from ..interactions import Append, Changed, Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


Variant = Literal["neutral", "info", "warn", "ok", "danger"]


class AlertRef(NudleRef):
    """Display banner ref. `write` carries partial updates; `notify` fires on user dismiss.

    Variant maps to the Alert primitive's `tone` (5 tones per kit): `neutral`
    picks the plain elevated surface, the rest attach the matching status
    wash / line / fg + auto icon. Default stays `info` to preserve wire
    behavior; the renderer falls back to `neutral` for unmapped values.
    """

    variant: ClassVar[str] = "info"
    title: ClassVar[str] = ""
    body: ClassVar[str] = ""
    dismissible: ClassVar[bool] = False

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "variant": cls.variant,
            "title": cls.title,
            "body": cls.body,
            "dismissible": cls.dismissible,
        }

    def set_variant(self, name: Variant | StrArg) -> Nu:
        return Write(self, DictForm.of(variant=name))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(title=text))

    def set_body(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(body=text))

    def set_dismissible(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(dismissible=flag))

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
        return Write(self, DictForm.of(**payload))

    def dismissed(self) -> Changed:
        return Changed(self)


Variant = Literal["info", "warn", "ok", "danger", "neutral"]


class BadgeRef(NudleRef):
    """Display-only badge ref. One `write` op carries every mutation.

    Variant maps to the Badge primitive's status tones; `neutral` becomes the
    kit `outline` (transparent bg, muted border) — closest visual to the
    previous gray chip.
    """

    label: ClassVar[str] = ""
    variant: ClassVar[str] = "neutral"

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "variant": cls.variant}

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(label=text))

    def set_variant(self, name: Variant | StrArg) -> Nu:
        return Write(self, DictForm.of(variant=name))

    def set(
        self,
        label: StrArg,
        variant: Variant | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not UNSET:
            payload["variant"] = variant
        return Write(self, DictForm.of(**payload))


class CodeBlockRef(NudleRef):
    """Display-only code block. One `write` carries a partial dict {code, language, show_copy}."""

    code: ClassVar[str] = ""
    language: ClassVar[str] = ""
    show_copy: ClassVar[bool] = True

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        props: dict[str, object] = {}
        if cls.code != "":
            props["code"] = cls.code
        if cls.language != "":
            props["language"] = cls.language
        if cls.show_copy is not True:
            props["show_copy"] = cls.show_copy
        return props

    def set(
        self,
        code: StrArg = UNSET,
        language: StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {}
        if code is not UNSET:
            payload["code"] = code
        if language is not UNSET:
            payload["language"] = language
        return Write(self, DictForm.of(**payload))

    def set_code(self, code: StrArg) -> Nu:
        return Write(self, DictForm.of(code=code))

    def set_language(self, language: StrArg) -> Nu:
        return Write(self, DictForm.of(language=language))


Align = Literal["left", "center", "right"]


class DividerRef(NudleRef):
    """Display-only divider ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    align: ClassVar[str] = "center"

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "align": cls.align}

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(label=text))

    def set_align(self, side: Align | StrArg) -> Nu:
        return Write(self, DictForm.of(align=side))

    def set(
        self,
        label: StrArg,
        align: Align | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if align is not UNSET:
            payload["align"] = align
        return Write(self, DictForm.of(**payload))


GaugeVariant = Literal["neutral", "ok", "warn", "danger"]


class GaugeRef(NudleRef):
    """Display-only gauge ref. One `write` op carries every mutation.

    Variant is the tone the arc reads with. `neutral` maps to the kit Gauge
    `accent` tone (brand purple); the other three map 1:1 to status tokens.
    """

    value: ClassVar[float] = 0.0
    caption: ClassVar[str] = ""
    variant: ClassVar[str] = "neutral"

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "caption": cls.caption,
            "variant": cls.variant,
        }

    def set_value(self, value: FloatArg) -> Nu:
        return Write(self, DictForm.of(value=value))

    def set_caption(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(caption=text))

    def set_variant(self, variant: GaugeVariant | StrArg) -> Nu:
        return Write(self, DictForm.of(variant=variant))

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
        return Write(self, DictForm.of(**payload))


Align = Literal["left", "center", "right"]


class HeadingRef(NudleRef):
    """Display-only heading ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    level: ClassVar[int] = 1
    align: ClassVar[str] = "left"

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "level": cls.level, "align": cls.align}

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(label=text))

    def set_level(self, n: IntArg) -> Nu:
        return Write(self, DictForm.of(level=n))

    def set_align(self, side: Align | StrArg) -> Nu:
        return Write(self, DictForm.of(align=side))

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
        return Write(self, DictForm.of(**payload))


Fit = Literal["contain", "cover", "fill"]


class ImageRef(NudleRef):
    """Display-only image ref. One `write` op carries every mutation."""

    src: ClassVar[str] = ""
    alt: ClassVar[str] = ""
    fit: ClassVar[str] = "contain"
    width: ClassVar[int | None] = None
    height: ClassVar[int | None] = None
    rounded: ClassVar[bool] = False

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        out: dict[str, object] = {}
        if cls.src != "":
            out["src"] = cls.src
        if cls.alt != "":
            out["alt"] = cls.alt
        if cls.fit != "contain":
            out["fit"] = cls.fit
        if cls.width is not None:
            out["width"] = cls.width
        if cls.height is not None:
            out["height"] = cls.height
        if cls.rounded:
            out["rounded"] = cls.rounded
        return out

    def set_src(self, url: StrArg) -> Nu:
        return Write(self, DictForm.of(src=url))

    def set_alt(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(alt=text))

    def set_fit(self, mode: Fit | StrArg) -> Nu:
        return Write(self, DictForm.of(fit=mode))

    def set_size(
        self,
        width: IntArg | None,
        height: IntArg | None,
    ) -> Nu:
        return Write(self, DictForm.of(width=width, height=height))

    def set_rounded(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(rounded=flag))

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
        return Write(self, DictForm.of(**payload))


Theme = Literal["light", "dark"]


class JsonViewerRef(NudleRef):
    """Display-only json viewer ref. One `write` op carries every mutation via partial-merge."""

    value: ClassVar[object] = None
    expand_depth: ClassVar[int] = 1
    theme: ClassVar[str] = "light"
    copyable: ClassVar[bool] = False
    sortable: ClassVar[bool] = False
    max_height: ClassVar[int | None] = None

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "expand_depth": cls.expand_depth,
            "theme": cls.theme,
            "copyable": cls.copyable,
            "sortable": cls.sortable,
            "max_height": cls.max_height,
        }

    def set_value(self, value: Arg[Any]) -> Nu:
        return Write(self, DictForm.of(value=value))

    def set_expand_depth(self, depth: IntArg) -> Nu:
        return Write(self, DictForm.of(expand_depth=depth))

    def set_theme(self, name: Theme | StrArg) -> Nu:
        return Write(self, DictForm.of(theme=name))

    def set_copyable(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(copyable=flag))

    def set_sortable(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(sortable=flag))

    def set_max_height(self, px: IntArg | None) -> Nu:
        return Write(self, DictForm.of(max_height=px))

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
        return Write(self, DictForm.of(**payload))


Target = Literal["_self", "_blank"]


class LinkRef(NudleRef):
    """Display-only link ref. One `write` op carries every mutation."""

    href: ClassVar[str] = ""
    label: ClassVar[str] = ""
    target: ClassVar[str] = "_self"
    external: ClassVar[bool | None] = None

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "href": cls.href,
            "label": cls.label,
            "target": cls.target,
            "external": cls.external,
        }

    def set_href(self, url: StrArg) -> Nu:
        return Write(self, DictForm.of(href=url))

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(label=text))

    def set_target(self, name: Target | StrArg) -> Nu:
        return Write(self, DictForm.of(target=name))

    def set_external(self, flag: BoolArg | None) -> Nu:
        return Write(self, DictForm.of(external=flag))

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
        return Write(self, DictForm.of(**payload))


class MarkdownRef(NudleRef):
    """Display-only markdown ref. Source string rendered as commonmark."""

    value: ClassVar[str] = ""

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        if cls.value == "":
            return {}
        return {"value": cls.value}

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)


class ProgressRef(NudleRef):
    """Display-only progress ref. One `write` op carries every mutation."""

    value: ClassVar[float] = 0.0
    caption: ClassVar[str] = ""
    indeterminate: ClassVar[bool] = False

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "caption": cls.caption,
            "indeterminate": cls.indeterminate,
        }

    def set_value(self, value: FloatArg) -> Nu:
        return Write(self, DictForm.of(value=value))

    def set_caption(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(caption=text))

    def set_indeterminate(self, flag: BoolArg) -> Nu:
        return Write(self, DictForm.of(indeterminate=flag))

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
        return Write(self, DictForm.of(**payload))


Trend = Literal["up", "down", "flat"]


class StatRef(NudleRef):
    """Display-only stat ref. Server-owned, single `write` op carries partial updates."""

    label: ClassVar[str] = ""
    value: ClassVar[str] = ""
    delta: ClassVar[str] = ""
    trend: ClassVar[str] = "flat"

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "value": cls.value,
            "delta": cls.delta,
            "trend": cls.trend,
        }

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(label=text))

    def set_value(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(value=text))

    def set_delta(self, text: StrArg) -> Nu:
        return Write(self, DictForm.of(delta=text))

    def set_trend(self, name: Trend | StrArg) -> Nu:
        return Write(self, DictForm.of(trend=name))


SortDirection = Literal["asc", "desc"]


class TableRef(NudleRef):
    """Tabular data; display by default, optional sortable headers and row click.

    Composes the kit Table primitive family. `dense=True` maps to the
    primitive's `compact` density; `striped=True` selects the `striped` variant.
    """

    columns: ClassVar[list[str]] = []
    striped: ClassVar[bool] = True
    dense: ClassVar[bool] = False
    max_rows: ClassVar[int] = 0
    sort_column: ClassVar[str] = ""
    sort_direction: ClassVar[str] = "asc"
    clickable_rows: ClassVar[bool] = False

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        return {
            "columns": list(cls.columns),
            "striped": cls.striped,
            "dense": cls.dense,
            "max_rows": cls.max_rows,
            "sort_column": cls.sort_column,
            "sort_direction": cls.sort_direction,
            "clickable_rows": cls.clickable_rows,
        }

    def set(self, table: DictArg[str, Any]) -> Nu:
        return Write(self, table)

    def clear(self) -> Nu:
        return Write(self, DictForm.of(rows=[]))

    def append(self, row: ListArg[Any]) -> Nu:
        return Append(self, row)

    def set_sort(self, column: StrArg, direction: SortDirection | StrArg) -> Nu:
        return Write(self, DictForm.of(sort_column=column, sort_direction=direction))

    def row_clicked(self) -> Changed:
        return Changed(self)


class TextRef(NudleRef):
    """Display-only string ref. Body copy."""

    value: ClassVar[str] = ""

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        if cls.value == "":
            return {}
        return {"value": cls.value}

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)


__all__ = [
    "AlertRef",
    "BadgeRef",
    "CodeBlockRef",
    "DividerRef",
    "GaugeRef",
    "HeadingRef",
    "ImageRef",
    "JsonViewerRef",
    "LinkRef",
    "MarkdownRef",
    "ProgressRef",
    "StatRef",
    "TableRef",
    "TextRef",
]
