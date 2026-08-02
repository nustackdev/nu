"""Display / output Refs -- server-owned sinks that render into the body.

Server pushes values via `write` / `append`; the browser only renders,
never reads back. See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Self

from nu import Dict
from nu.lang.sentinels import UNSET
from nu.ui.core import Append, Changed, Ref, Write


if TYPE_CHECKING:
    from nu import Nu
    from nu.lang.args import Arg, BoolArg, DictArg, FloatArg, IntArg, ListArg, StrArg


Variant = Literal["neutral", "info", "warn", "ok", "danger"]


class AlertRef(Ref):
    """Display banner ref. `write` carries partial updates; `notify` fires on user dismiss.

    Variant maps to the Alert primitive's `tone` (5 tones per kit): `neutral`
    picks the plain elevated surface, the rest attach the matching status
    wash / line / fg + auto icon. Default stays `info` to preserve wire
    behavior; the renderer falls back to `neutral` for unmapped values.
    """

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

    def dismissed(self) -> Changed:
        return Changed(self)


Variant = Literal["info", "warn", "ok", "danger", "neutral"]


class BadgeRef(Ref):
    """Display-only badge ref. One `write` op carries every mutation.

    Variant maps to the Badge primitive's status tones; `neutral` becomes the
    kit `outline` (transparent bg, muted border) — closest visual to the
    previous gray chip.
    """

    @classmethod
    def slot(cls, *, label: str = "", variant: Variant = "neutral") -> Self:
        return super().slot(label=label, variant=variant)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_variant(self, name: Variant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set(
        self,
        label: StrArg,
        variant: Variant | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not UNSET:
            payload["variant"] = variant
        return Write(self, Dict.of(**payload))


class CodeBlockRef(Ref):
    """Display-only code block. One `write` carries a partial dict {code, language, show_copy}."""

    @classmethod
    def slot(
        cls,
        *,
        code: str = "",
        language: str = "",
        show_copy: bool = True,
    ) -> Self:
        return super().slot(code=code, language=language, show_copy=show_copy)

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
        return Write(self, Dict.of(**payload))

    def set_code(self, code: StrArg) -> Nu:
        return Write(self, Dict.of(code=code))

    def set_language(self, language: StrArg) -> Nu:
        return Write(self, Dict.of(language=language))


Align = Literal["left", "center", "right"]


class DividerRef(Ref):
    """Display-only divider ref. One `write` op carries every mutation."""

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


GaugeVariant = Literal["neutral", "ok", "warn", "danger"]


class GaugeRef(Ref):
    """Display-only gauge ref. One `write` op carries every mutation.

    Variant is the tone the arc reads with. `neutral` maps to the kit Gauge
    `accent` tone (brand purple); the other three map 1:1 to status tokens.
    """

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


Target = Literal["_self", "_blank"]


class LinkRef(Ref):
    """Display-only link ref. One `write` op carries every mutation."""

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


class MarkdownRef(Ref):
    """Display-only markdown ref. Source string rendered as commonmark."""

    @classmethod
    def slot(cls, *, value: str = "") -> Self:
        return super().slot(value=value)

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)


class ProgressRef(Ref):
    """Display-only progress ref. One `write` op carries every mutation."""

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


SortDirection = Literal["asc", "desc"]


class TableRef(Ref):
    """Tabular data; display by default, optional sortable headers and row click.

    Composes the kit Table primitive family. `dense=True` maps to the
    primitive's `compact` density; `striped=True` selects the `striped` variant.
    """

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

    def row_clicked(self) -> Changed:
        return Changed(self)


class TextRef(Ref):
    """Display-only string ref. Body copy."""

    @classmethod
    def slot(cls, *, value: str = "") -> Self:
        return super().slot(value=value)

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
