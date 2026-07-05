"""Display / output Refs -- server-owned sinks that render into the body.

Server pushes values via `write` / `append`; the browser only renders,
never reads back. See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from nu import DictForm

from ..interactions import Append, Changed, Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


Variant = Literal["info", "warn", "ok", "danger"]


class AlertRef(NudleRef):
    """Display banner ref. `write` carries partial updates; `notify` fires on user dismiss."""

    variant: ClassVar[str] = "info"
    title: ClassVar[str] = ""
    body: ClassVar[str] = ""
    dismissible: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "variant": cls.variant,
            "title": cls.title,
            "body": cls.body,
            "dismissible": cls.dismissible,
        }

    def store_variant(self, name: Nu | Variant | str) -> Nu:
        return Write(self, DictForm.of(variant=name))

    def store_title(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(title=text))

    def store_body(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(body=text))

    def store_dismissible(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(dismissible=flag))

    def store(
        self,
        title: Nu | str,
        body: Nu | str | None = None,
        variant: Nu | Variant | str | None = None,
        dismissible: Nu | bool | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"title": title}
        if body is not None:
            payload["body"] = body
        if variant is not None:
            payload["variant"] = variant
        if dismissible is not None:
            payload["dismissible"] = dismissible
        return Write(self, DictForm.of(**payload))

    def dismissed(self) -> Changed:
        return Changed(self)


Variant = Literal["info", "warn", "ok", "danger", "neutral"]


class BadgeRef(NudleRef):
    """Display-only badge ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    variant: ClassVar[str] = "neutral"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "variant": cls.variant}

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_variant(self, name: Nu | Variant | str) -> Nu:
        return Write(self, DictForm.of(variant=name))

    def store(
        self,
        label: Nu | str,
        variant: Nu | Variant | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not None:
            payload["variant"] = variant
        return Write(self, DictForm.of(**payload))


class CodeBlockRef(NudleRef):
    """Display-only code block. One `write` op carries a partial dict of {code, language, show_copy}."""

    code: ClassVar[str] = ""
    language: ClassVar[str] = ""
    show_copy: ClassVar[bool] = True

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        props: dict[str, object] = {}
        if cls.code != "":
            props["code"] = cls.code
        if cls.language != "":
            props["language"] = cls.language
        if cls.show_copy is not True:
            props["show_copy"] = cls.show_copy
        return props

    def store(
        self,
        code: Nu | str | None = None,
        language: Nu | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {}
        if code is not None:
            payload["code"] = code
        if language is not None:
            payload["language"] = language
        return Write(self, DictForm.of(**payload))

    def store_code(self, code: Nu | str) -> Nu:
        return Write(self, DictForm.of(code=code))

    def store_language(self, language: Nu | str) -> Nu:
        return Write(self, DictForm.of(language=language))


Align = Literal["left", "center", "right"]


class DividerRef(NudleRef):
    """Display-only divider ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    align: ClassVar[str] = "center"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "align": cls.align}

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_align(self, side: Nu | Align | str) -> Nu:
        return Write(self, DictForm.of(align=side))

    def store(
        self,
        label: Nu | str,
        align: Nu | Align | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if align is not None:
            payload["align"] = align
        return Write(self, DictForm.of(**payload))


class GaugeRef(NudleRef):
    """Display-only gauge ref. One `write` op carries every mutation."""

    value: ClassVar[float] = 0.0
    caption: ClassVar[str] = ""
    variant: ClassVar[str] = "neutral"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "caption": cls.caption,
            "variant": cls.variant,
        }

    def store_value(self, value: Nu | float) -> Nu:
        return Write(self, DictForm.of(value=value))

    def store_caption(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(caption=text))

    def store_variant(self, variant: Nu | str) -> Nu:
        return Write(self, DictForm.of(variant=variant))

    def store(
        self,
        value: Nu | float,
        caption: Nu | str | None = None,
        variant: Nu | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if caption is not None:
            payload["caption"] = caption
        if variant is not None:
            payload["variant"] = variant
        return Write(self, DictForm.of(**payload))


Align = Literal["left", "center", "right"]


class HeadingRef(NudleRef):
    """Display-only heading ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    level: ClassVar[int] = 1
    align: ClassVar[str] = "left"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "level": cls.level, "align": cls.align}

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_level(self, n: Nu | int) -> Nu:
        return Write(self, DictForm.of(level=n))

    def store_align(self, side: Nu | Align | str) -> Nu:
        return Write(self, DictForm.of(align=side))

    def store(
        self,
        label: Nu | str,
        level: Nu | int | None = None,
        align: Nu | Align | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if level is not None:
            payload["level"] = level
        if align is not None:
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
    def mount_props(cls) -> dict[str, object]:
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

    def store_src(self, url: Nu | str) -> Nu:
        return Write(self, DictForm.of(src=url))

    def store_alt(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(alt=text))

    def store_fit(self, mode: Nu | Fit | str) -> Nu:
        return Write(self, DictForm.of(fit=mode))

    def store_size(
        self,
        width: Nu | int | None,
        height: Nu | int | None,
    ) -> Nu:
        return Write(self, DictForm.of(width=width, height=height))

    def store_rounded(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(rounded=flag))

    def store(
        self,
        src: Nu | str,
        alt: Nu | str | None = None,
        fit: Nu | Fit | str | None = None,
        width: Nu | int | None = None,
        height: Nu | int | None = None,
        rounded: Nu | bool | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"src": src}
        if alt is not None:
            payload["alt"] = alt
        if fit is not None:
            payload["fit"] = fit
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if rounded is not None:
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
    def mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "expand_depth": cls.expand_depth,
            "theme": cls.theme,
            "copyable": cls.copyable,
            "sortable": cls.sortable,
            "max_height": cls.max_height,
        }

    def store_value(self, value: Nu | object) -> Nu:
        return Write(self, DictForm.of(value=value))

    def store_expand_depth(self, depth: Nu | int) -> Nu:
        return Write(self, DictForm.of(expand_depth=depth))

    def store_theme(self, name: Nu | Theme | str) -> Nu:
        return Write(self, DictForm.of(theme=name))

    def store_copyable(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(copyable=flag))

    def store_sortable(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(sortable=flag))

    def store_max_height(self, px: Nu | int | None) -> Nu:
        return Write(self, DictForm.of(max_height=px))

    def store(
        self,
        value: Nu | object,
        expand_depth: Nu | int | None = None,
        theme: Nu | Theme | str | None = None,
        copyable: Nu | bool | None = None,
        sortable: Nu | bool | None = None,
        max_height: Nu | int | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if expand_depth is not None:
            payload["expand_depth"] = expand_depth
        if theme is not None:
            payload["theme"] = theme
        if copyable is not None:
            payload["copyable"] = copyable
        if sortable is not None:
            payload["sortable"] = sortable
        if max_height is not None:
            payload["max_height"] = max_height
        return Write(self, DictForm.of(**payload))


Target = Literal["_self", "_blank"]

_UNSET: object = object()


class LinkRef(NudleRef):
    """Display-only link ref. One `write` op carries every mutation."""

    href: ClassVar[str] = ""
    label: ClassVar[str] = ""
    target: ClassVar[str] = "_self"
    external: ClassVar[bool | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "href": cls.href,
            "label": cls.label,
            "target": cls.target,
            "external": cls.external,
        }

    def store_href(self, url: Nu | str) -> Nu:
        return Write(self, DictForm.of(href=url))

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_target(self, name: Nu | Target | str) -> Nu:
        return Write(self, DictForm.of(target=name))

    def store_external(self, flag: Nu | bool | None) -> Nu:
        return Write(self, DictForm.of(external=flag))

    def store(
        self,
        href: Nu | str | object = _UNSET,
        label: Nu | str | object = _UNSET,
        target: Nu | Target | str | object = _UNSET,
        external: Nu | bool | None | object = _UNSET,
    ) -> Nu:
        # Sentinel-based kwargs so callers can pass `external=None` (auto)
        # without conflating it with "do not touch this field".
        payload: dict[str, object] = {}
        if href is not _UNSET:
            payload["href"] = href
        if label is not _UNSET:
            payload["label"] = label
        if target is not _UNSET:
            payload["target"] = target
        if external is not _UNSET:
            payload["external"] = external
        return Write(self, DictForm.of(**payload))


class MarkdownRef(NudleRef):
    """Display-only markdown ref. Source string rendered as commonmark."""

    value: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        if cls.value == "":
            return {}
        return {"value": cls.value}

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)


class ProgressRef(NudleRef):
    """Display-only progress ref. One `write` op carries every mutation."""

    value: ClassVar[float] = 0.0
    caption: ClassVar[str] = ""
    indeterminate: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "caption": cls.caption,
            "indeterminate": cls.indeterminate,
        }

    def store_value(self, value: Nu | float) -> Nu:
        return Write(self, DictForm.of(value=value))

    def store_caption(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(caption=text))

    def store_indeterminate(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(indeterminate=flag))

    def store(
        self,
        value: Nu | float,
        caption: Nu | str | None = None,
        indeterminate: Nu | bool | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if caption is not None:
            payload["caption"] = caption
        if indeterminate is not None:
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
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "value": cls.value,
            "delta": cls.delta,
            "trend": cls.trend,
        }

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_value(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(value=text))

    def store_delta(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(delta=text))

    def store_trend(self, name: Nu | Trend | str) -> Nu:
        return Write(self, DictForm.of(trend=name))


class TableRef(NudleRef):
    """Tabular data; display by default, optional sortable headers and row click."""

    columns: ClassVar[list[str]] = []
    striped: ClassVar[bool] = True
    dense: ClassVar[bool] = False
    max_rows: ClassVar[int] = 0
    sort_column: ClassVar[str] = ""
    sort_direction: ClassVar[str] = "asc"
    clickable_rows: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "columns": list(cls.columns),
            "striped": cls.striped,
            "dense": cls.dense,
            "max_rows": cls.max_rows,
            "sort_column": cls.sort_column,
            "sort_direction": cls.sort_direction,
            "clickable_rows": cls.clickable_rows,
        }

    def store(self, table: Nu | dict[str, Any]) -> Nu:
        return Write(self, table)

    def clear(self) -> Nu:
        return Write(self, DictForm.of(rows=[]))

    def append(self, row: Nu | list[Any]) -> Nu:
        return Append(self, row)

    def store_sort(self, column: Nu | str, direction: Nu | str) -> Nu:
        return Write(self, DictForm.of(sort_column=column, sort_direction=direction))

    def row_clicked(self) -> Changed:
        return Changed(self)


class TextRef(NudleRef):
    """Display-only string ref. Body copy."""

    value: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        if cls.value == "":
            return {}
        return {"value": cls.value}

    def store(self, value: Nu | str) -> Nu:
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
