"""Input Refs -- tab-owned; server reads via `read` + `notify` path.

Also home to the two Refs with both faces, `MarkdownRef` and `CodeRef`:
read-only by default, editable on request, readable either way.

The browser owns the live value. Host reads via `Ref` (round-trip
through session), subscribes via `.on_change()` / `.on_submit()` /
`.on_click()`.

The contract every input shares (``InputLeaf``):

- the seed is ``value=`` at the slot, whatever the value's kind (text, a
  bool, a pick, a list), and ``set(value)`` writes it; ``reset()`` puts the
  seed back;
- every notify names its event: ``on_change()`` hears ``{event: "change"}``,
  sent when a value is committed and only when it moved (blur, Enter, a
  pick, a toggle, a release); ``on_submit()`` hears ``{event: "submit"}``,
  sent when the person asks to send (Enter in a single-line field,
  cmd/ctrl+Enter in a multi-line one). Enter that changed the value sends
  the change first, then the submit;
- the common props: ``label``, ``disabled``, ``readonly``, ``required``,
  ``autofocus`` and ``size``, with ``set_label``, ``set_disabled``,
  ``set_readonly`` and ``set_required``. Inside a ``Field`` the Field labels
  the control, and its help, error and required land on the control itself.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Changed, Reset, Write

from ..vocab import ControlSize, Target
from ..vocab import set_href as _set_href
from .base import LeafRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.args import BoolArg, FloatArg, ListArg, StrArg
    from nu.lang.runtime import Runtime


#: The event an input sends when a value is committed.
CHANGE = "change"
#: The event an input sends when the person asks to send what it holds.
SUBMIT = "submit"
#: The event a button sends on a click.
CLICK = "click"


Variant = Literal["primary", "secondary", "outline", "ghost", "soft", "danger", "link"]


def _common(
    *,
    label: str,
    disabled: bool,
    readonly: bool,
    required: bool,
    autofocus: bool,
    size: ControlSize,
) -> dict[str, object]:
    """The props every input declares, in one place."""
    return {
        "label": label,
        "disabled": bool(disabled),
        "readonly": bool(readonly),
        "required": bool(required),
        "autofocus": bool(autofocus),
        "size": size,
    }


class InputLeaf(LeafRef):
    """What every input Ref is: a live value in the browser, read, written, heard.

    Abstract. Reading the Ref is a round trip for the live value. ``set``
    writes it, ``reset`` puts the slot's ``value=`` back, ``on_change`` hears
    each committed change. The common props have their setters here.
    """

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: Any) -> Nu:
        return Write(self, value)

    def reset(self) -> Nu:
        """Put the value the slot declared back. Sends no change."""
        return Reset(self)

    def on_change(self) -> Changed:
        """Each committed change: blur, Enter, a pick, a toggle. Never per keystroke."""
        return Changed(self, CHANGE)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_disabled(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(disabled=flag))

    def set_readonly(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(readonly=flag))

    def set_required(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(required=flag))


class _Submits:
    """Mixin: the input has a send key, heard by ``on_submit()``."""

    def on_submit(self) -> Changed:
        """The person asked to send: Enter, or cmd/ctrl+Enter in a multi-line field."""
        return Changed(self, SUBMIT)  # type: ignore[arg-type]


class _Placeholder:
    """Mixin: the input shows a placeholder while empty."""

    def set_placeholder(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(placeholder=text))  # type: ignore[arg-type]


class ButtonRef(LeafRef):
    """Click trigger; subscribe via `.on_click()`.

    `size` runs 20, 24, 32 and 40 px tall, the icon-only square too. `link`
    is the text-link look on a button. With `href` the button is a real
    anchor wearing the button look, so cmd-click opens a tab and a host that
    routes its own links routes this one; a click still reaches `.on_click()`.
    For a link that should read as one, `LinkRef` takes button looks too.

    `icon` names a lucide icon in kebab case, drawn before the label. With an
    empty label the button draws as a square icon button, named for screen
    readers by `tooltip` (or the icon name when there is none). `tooltip` is
    the hover hint, shown whenever it is set.

    Inside a Form a button submits only with `submit=True`; every other
    button is a plain one, so a Cancel never submits. The Form's submit
    payload names the submit button that fired by its slot name. `loading`
    draws a spinner in place of the icon and takes no clicks; a Form that is
    busy spins its submit buttons on its own.

    Any lucide name draws (https://lucide.dev/icons), the same names every
    Ref with an `icon` takes. An unknown name draws the label alone.
    """

    _wire_type = "ButtonRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        variant: Variant = "primary",
        disabled: bool = False,
        icon: str = "",
        tooltip: str = "",
        size: ControlSize = "md",
        href: str = "",
        target: Target = "_self",
        submit: bool = False,
        loading: bool = False,
        autofocus: bool = False,
    ) -> Self:
        return super().slot(
            label=label,
            variant=variant,
            disabled=disabled,
            icon=icon,
            tooltip=tooltip,
            size=size,
            href=href,
            target=target,
            submit=bool(submit),
            loading=bool(loading),
            autofocus=bool(autofocus),
        )

    def on_click(self) -> Changed:
        return Changed(self, CLICK)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_variant(self, name: Variant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set_disabled(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(disabled=flag))

    def set_loading(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(loading=flag))

    def set_icon(self, name: StrArg) -> Nu:
        return Write(self, Dict.of(icon=name))

    def set_tooltip(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(tooltip=text))

    def set_size(self, name: ControlSize | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set_href(self, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
        """Point the button somewhere; an empty url makes it a plain trigger again."""
        return _set_href(self, url, target)

    def set(
        self,
        label: StrArg,
        variant: Variant | StrArg = UNSET,
        disabled: BoolArg = UNSET,
        icon: StrArg = UNSET,
        tooltip: StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not UNSET:
            payload["variant"] = variant
        if disabled is not UNSET:
            payload["disabled"] = disabled
        if icon is not UNSET:
            payload["icon"] = icon
        if tooltip is not UNSET:
            payload["tooltip"] = tooltip
        return Write(self, Dict.of(**payload))


class CheckboxRef(InputLeaf):
    """Boolean toggle whose checked state lives in the browser."""

    _wire_type = "CheckboxRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        value: bool = False,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            value=bool(value),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: BoolArg) -> Nu:
        return Write(self, value)


class DatePickerRef(_Submits, _Placeholder, InputLeaf):
    """Date input whose ISO yyyy-mm-dd value lives in the browser ("" for none).

    A pick is a change. Enter on the closed picker submits; Space and the
    down arrow open the calendar.
    """

    _wire_type = "DatePickerRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        min: str = "",
        max: str = "",
        value: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            placeholder=placeholder,
            min=min,
            max=max,
            value=value,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)


InputType = Literal["text", "password", "email", "number"]


class InputRef(_Submits, _Placeholder, InputLeaf):
    """Text input whose value lives in the browser.

    A read sees what is under the caret. Blur commits (a change, when the
    text moved), Enter commits and submits, and focus stays in the field.
    `clear_on_submit` puts the seed back after each submit, for a field you
    type into, send, and type into again.

    Default face is display (Inter); code-shaped fields opt into
    JetBrains Mono via `mono=True`, which flips `font-mono` at render time.
    """

    _wire_type = "InputRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        value: str = "",
        type: InputType = "text",
        max_length: int | None = None,
        mono: bool = False,
        clear_on_submit: bool = False,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            placeholder=placeholder,
            value=value,
            type=type,
            max_length=max_length,
            mono=mono,
            clear_on_submit=bool(clear_on_submit),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)


class CodeRef(_Submits, InputLeaf):
    """Source code, read-only by default. Value is the text, both ways.

    Read-only it renders a highlighted block with a copy button. With
    `editable=True` the same view becomes an editor: the server seeds the text
    with `set`, reads it back through `Ref` like any input Ref, and subscribes
    with `on_change()`. The browser commits on cmd+enter and on blur, not on
    every keystroke, so a read between commits sees the last committed text
    and not what is under the caret. cmd+enter also submits (`on_submit()`).
    One engine for both modes, so flipping `editable` never changes how the
    code looks.

    Last actor wins, same as `MarkdownRef`. A `set` from the server replaces
    the buffer outright, a notify from the browser replaces the server's
    copy, and there is no merge.

    Args:
        language: a language name or alias (`python`, `sql`, `markdown`,
            `shell`, `yaml`, `ts`, `json`, ...). Anything unknown renders
            unhighlighted rather than failing.
        line_numbers: `None` follows the mode, numbered while editable and
            bare while read-only.
        wrap: soft-wrap long lines instead of scrolling sideways.
        show_copy: the copy button, shown only while read-only.
        min_height, max_height: pixels. The view grows with its content
            between the bounds, then scrolls. `None` is no bound.
    """

    _wire_type = "CodeRef"

    @classmethod
    def slot(
        cls,
        *,
        value: str = "",
        language: str = "",
        editable: bool = False,
        line_numbers: bool | None = None,
        wrap: bool = False,
        show_copy: bool = True,
        min_height: int | None = None,
        max_height: int | None = None,
    ) -> Self:
        return super().slot(
            value=value,
            language=language,
            editable=editable,
            line_numbers=line_numbers,
            wrap=wrap,
            show_copy=show_copy,
            min_height=min_height,
            max_height=max_height,
        )

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def set_language(self, name: StrArg) -> Nu:
        return Write(self, Dict.of(language=name))

    def set_editable(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(editable=flag))


class NumberInputRef(_Submits, _Placeholder, InputLeaf):
    """Numeric input whose value lives in the browser.

    Typing is local; blur, Enter, a stepper click or an arrow key commits.
    Enter also submits.
    """

    _wire_type = "NumberInputRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        min: float | None = None,
        max: float | None = None,
        step: float = 1.0,
        value: float = 0.0,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            placeholder=placeholder,
            min=min,
            max=max,
            step=step,
            value=value,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set_min(self, value: FloatArg | None) -> Nu:
        return Write(self, Dict.of(min=value))

    def set_max(self, value: FloatArg | None) -> Nu:
        return Write(self, Dict.of(max=value))

    def set_step(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(step=value))

    def set(
        self,
        value: FloatArg,
        min: FloatArg = UNSET,
        max: FloatArg = UNSET,
        step: FloatArg = UNSET,
        label: StrArg = UNSET,
    ) -> Nu:
        # Scalar shortcut: just the number when no extra kwargs are passed.
        if min is UNSET and max is UNSET and step is UNSET and label is UNSET:
            return Write(self, value)
        payload: dict[str, object] = {"value": value}
        if min is not UNSET:
            payload["min"] = min
        if max is not UNSET:
            payload["max"] = max
        if step is not UNSET:
            payload["step"] = step
        if label is not UNSET:
            payload["label"] = label
        return Write(self, Dict.of(**payload))


class MarkdownRef(_Placeholder, InputLeaf):
    """A markdown document, read-only by default. Value is the markdown, both ways.

    The browser never shows the source. Read-only it renders the document;
    with `editable=True` the same view becomes a live wysiwyg editor: the
    server writes the source with `set`, reads it back through `Ref` like any
    input Ref, and subscribes with `on_change()`. The browser notifies back
    on a quiet moment or on blur. One engine for both modes, so a document
    looks the same whether or not you can type in it. A document saves
    itself, so it has no send key and no `on_submit()`.

    The dialect: paragraphs, headings, bullet, numbered and checkbox lists,
    quotes, code fences, GFM pipe tables, rules, images, bold, italic, inline
    code and links. Code fences are syntax highlighted, with a language picker
    when editable. Table cells hold inline content only, a pipe inside one is
    backslash-escaped, and the editor writes every table in one form (outer
    pipes, one space of padding, `---` / `:---` / `:---:` / `---:` delimiters).

    Last actor wins. There is no merge, no OT, no CRDT: a `set` from the
    server replaces the document outright, and a notify from the browser
    replaces the server's copy. Two people typing into the same Ref at the
    same time will clobber each other, by design.
    """

    _wire_type = "MarkdownRef"

    @classmethod
    def slot(
        cls,
        *,
        value: str = "",
        placeholder: str = "",
        editable: bool = False,
    ) -> Self:
        return super().slot(value=value, placeholder=placeholder, editable=editable)

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def set_editable(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(editable=flag))


def _normalize_options(opts: object) -> list[dict[str, str]]:
    """Accept ["a", "b"] or [{"value": "a", "label": "A"}] and return the dict form."""
    if not isinstance(opts, list):
        return []
    out: list[dict[str, str]] = []
    for item in opts:
        if isinstance(item, str):
            out.append({"value": item, "label": item})
        elif isinstance(item, dict):
            value = str(item.get("value", "")) if item.get("value") is not None else ""
            label = str(item.get("label", value)) if item.get("label") is not None else value
            out.append({"value": value, "label": label})
    return out


def _options_write(ref: InputLeaf, opts: object) -> Nu:
    """The ``set_options`` write: a literal list normalized here, a term as it is."""
    if isinstance(opts, list):
        payload: object = {"options": _normalize_options(opts)}
    else:
        payload = {"options": opts}
    return Write(ref, Dict.of(**payload))


Orientation = Literal["vertical", "horizontal"]


class RadioGroupRef(InputLeaf):
    """Single-choice radio group whose value lives in the browser ("" for none).

    `label` names the group (or the Field around it does).
    """

    _wire_type = "RadioGroupRef"

    @classmethod
    def slot(
        cls,
        *,
        options: list[str] | list[dict[str, str]] | None = None,
        value: str = "",
        orientation: Orientation = "vertical",
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            value=value,
            orientation=orientation,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        return _options_write(self, opts)


class SelectRef(_Placeholder, InputLeaf):
    """Dropdown single-select whose value lives in the browser ("" for none).

    `searchable=True` swaps the picker for one with a filter field, for long
    option lists. Options, value, reads and notifies stay the same.
    """

    _wire_type = "SelectRef"

    @classmethod
    def slot(
        cls,
        *,
        options: list[str] | list[dict[str, str]] | None = None,
        value: str = "",
        placeholder: str = "",
        searchable: bool = False,
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            value=value,
            placeholder=placeholder,
            searchable=searchable,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        return _options_write(self, opts)

    def set_searchable(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(searchable=flag))


SketchTool = Literal["pen", "rect", "ellipse", "line", "arrow"]
SketchControl = Literal["tools", "stroke", "fill", "size", "undo", "redo", "clear"]

#: Every tool a board can offer, in toolbar order.
SKETCH_TOOLS: tuple[str, ...] = ("pen", "rect", "ellipse", "line", "arrow")
#: Every toolbar item, in toolbar order.
SKETCH_CONTROLS: tuple[str, ...] = ("tools", "stroke", "fill", "size", "undo", "redo", "clear")
_DEFAULT_KEYS = ("tool", "stroke", "fill", "size")


def _num(v: object) -> float | None:
    if isinstance(v, bool):
        return None
    try:
        n = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) else None


def _clamp(n: float) -> float:
    return min(max(n, 0.0), 1.0)


def _points(raw: object, *, pressure: bool) -> list[list[float]]:
    if not isinstance(raw, list | tuple):
        return []
    out: list[list[float]] = []
    for p in raw:
        if not isinstance(p, list | tuple) or len(p) < 2:
            continue
        x, y = _num(p[0]), _num(p[1])
        if x is None or y is None:
            continue
        pt = [_clamp(x), _clamp(y)]
        if pressure and len(p) > 2 and (pr := _num(p[2])) is not None:
            pt.append(_clamp(pr))
        out.append(pt)
    return out


def _style(el: dict, out: dict[str, Any], *, fill: bool) -> dict[str, Any]:
    """Carry the optional style fields over when they are well-formed."""
    keys = ("stroke", "fill") if fill else ("stroke",)
    for key in keys:
        v = el.get(key)
        if isinstance(v, str) and v.strip():
            out[key] = v.strip()
    w = _num(el.get("width"))
    if w is not None and w > 0:
        out["width"] = min(w, 1.0)
    return out


def _normalize_element(raw: object) -> dict[str, Any] | None:
    # A bare list of points is a pen stroke: the first sketch pad's value.
    if isinstance(raw, list | tuple):
        raw = {"type": "path", "points": raw}
    if not isinstance(raw, dict):
        return None
    kind = raw.get("type")
    if kind == "path":
        pts = _points(raw.get("points"), pressure=True)
        return _style(raw, {"type": "path", "points": pts}, fill=False) if pts else None
    if kind in ("rect", "ellipse"):
        x, y, w, h = (_num(raw.get(k)) for k in ("x", "y", "w", "h"))
        if x is None or y is None or w is None or h is None:
            return None
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        x, y = _clamp(x), _clamp(y)
        w, h = min(w, 1.0 - x), min(h, 1.0 - y)
        if w <= 0 and h <= 0:
            return None
        return _style(raw, {"type": kind, "x": x, "y": y, "w": w, "h": h}, fill=True)
    if kind in ("line", "arrow"):
        pts = _points(raw.get("points"), pressure=False)
        if len(pts) < 2:
            return None
        return _style(raw, {"type": kind, "points": [pts[0], pts[-1]]}, fill=False)
    return None


def _normalize_elements(raw: object) -> list[dict[str, Any]]:
    """Elements as plain dicts of the documented shape; anything off-shape dropped.

    Coordinates clamp to 0..1, a rect or ellipse with a negative side flips to
    a positive one, a line keeps its two ends, and a bare list of points is a
    pen stroke. Style fields (``stroke``, ``fill``, ``width``) are kept when
    well-formed and left out otherwise: the board fills them from its
    defaults, so what the browser hands back always carries them.
    """
    if not isinstance(raw, list | tuple):
        return []
    return [el for item in raw if (el := _normalize_element(item)) is not None]


def _subset(name: str, given: object, allowed: tuple[str, ...]) -> list[str]:
    if given is None:
        return list(allowed)
    if isinstance(given, str) or not isinstance(given, list | tuple):
        raise TypeError(f"SketchRef {name} takes a list of names from {allowed}")
    unknown = [g for g in given if g not in allowed]
    if unknown:
        raise ValueError(f"SketchRef {name}: unknown {unknown}; pick from {allowed}")
    # Toolbar order, whatever order they were named in.
    return [a for a in allowed if a in given]


class SketchRef(InputLeaf):
    """A board a person draws on with a pointer; the elements live in the browser.

    Pen ink (pressure-aware from a pen), rects, ellipses, lines and arrows,
    with a small floating toolbar for the tool, colors, size, undo, redo and
    clear. A program draws on it too: write elements and they appear.

    The value is a list of elements, every coordinate normalized to 0..1 of
    the board with the origin top-left, ``width`` a fraction of the board's
    shorter side::

        {"type": "path", "points": [[x, y], [x, y, pressure], ...], "stroke": "ink", "width": 0.012}
        {"type": "rect" | "ellipse", "x": .., "y": .., "w": .., "h": .., "stroke": .., "fill": .., "width": ..}
        {"type": "line" | "arrow", "points": [[x1, y1], [x2, y2]], "stroke": .., "width": ..}

    A color is a palette name that follows the theme (``ink``, ``gray``,
    ``red``, ``amber``, ``green``, ``blue``, ``violet``, each also as
    ``<name>-soft`` for fills) or any CSS color (``"#e11d48"``). ``"none"`` is
    no fill. A written element may leave out ``stroke``, ``fill`` and
    ``width``; the board fills them from ``defaults``, so a read always has
    them.

    The browser sends once per element, when the pointer lifts, and once per
    undo, redo and clear, so ``on_change()`` fires on those and never per
    move. ``set(elements)`` draws from the server, ``set([])`` or ``clear()``
    wipes, and reading the Ref gives the elements. Last actor wins: a ``set``
    replaces the board outright and starts its undo history over.

    Args:
        width: board width in px. It never grows past its container.
        height: board height in px; ``None`` is square. The aspect holds as it
            shrinks.
        tools: which tools exist, from ``pen``, ``rect``, ``ellipse``,
            ``line``, ``arrow``. ``None`` is all of them.
        controls: which toolbar items show, from ``tools``, ``stroke``,
            ``fill``, ``size``, ``undo``, ``redo``, ``clear``. ``None`` is all
            of them, ``[]`` is no toolbar.
        defaults: where the board starts: ``tool``, ``stroke``, ``fill`` and
            ``size`` (a width fraction). Unset keys keep the board's own
            (``pen``, ``ink``, ``none``, ``0.012``).
        readonly: draws the value and takes no input, no toolbar.
        label: drawn above the board, and its accessible name.
        value: elements to start with.
    """

    _wire_type = "SketchRef"

    @classmethod
    def slot(
        cls,
        *,
        width: int = 280,
        height: int | None = None,
        tools: list[SketchTool] | None = None,
        controls: list[SketchControl] | None = None,
        defaults: dict[str, object] | None = None,
        readonly: bool = False,
        label: str = "",
        value: list[dict[str, Any]] | None = None,
    ) -> Self:
        enabled = _subset("tools", tools, SKETCH_TOOLS)
        if not enabled:
            raise ValueError("SketchRef tools: name at least one tool")
        shown = _subset("controls", controls, SKETCH_CONTROLS)
        start = dict(defaults or {})
        unknown = [k for k in start if k not in _DEFAULT_KEYS]
        if unknown:
            raise ValueError(f"SketchRef defaults: unknown {unknown}; pick from {_DEFAULT_KEYS}")
        if "tool" in start and start["tool"] not in enabled:
            raise ValueError(
                f"SketchRef defaults: tool {start['tool']!r} is not in tools {enabled}"
            )
        if "size" in start:
            size = _num(start["size"])
            if size is None or size <= 0:
                raise ValueError("SketchRef defaults: size is a positive fraction of the board")
            start["size"] = size
        return super().slot(
            width=int(width),
            height=None if height is None else int(height),
            tools=enabled,
            controls=shown,
            defaults=start,
            readonly=bool(readonly),
            label=label,
            value=_normalize_elements(value or []),
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def _lift(self, raw: object) -> list[dict[str, Any]]:
        return _normalize_elements(raw)

    def set(self, elements: ListArg[dict[str, Any]]) -> Nu:
        if isinstance(elements, list | tuple):
            return Write(self, _normalize_elements(elements))
        return Write(self, elements)

    def clear(self) -> Nu:
        return Write(self, [])


class SliderRef(InputLeaf):
    """Numeric slider whose value lives in the browser.

    Dragging is local; the release (or an arrow key) commits.
    """

    _wire_type = "SliderRef"

    @classmethod
    def slot(
        cls,
        *,
        min: float = 0.0,
        max: float = 100.0,
        step: float = 1.0,
        value: float = 0.0,
        label: str = "",
        show_value: bool = True,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            min=min,
            max=max,
            step=step,
            value=value,
            show_value=show_value,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set_min(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(min=value))

    def set_max(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(max=value))

    def set_step(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(step=value))

    def set_show_value(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(show_value=flag))

    def set(
        self,
        value: FloatArg,
        min: FloatArg = UNSET,
        max: FloatArg = UNSET,
        step: FloatArg = UNSET,
        label: StrArg = UNSET,
        show_value: BoolArg = UNSET,
    ) -> Nu:
        # Scalar shortcut: just the number when no extra kwargs are passed.
        if all(x is UNSET for x in (min, max, step, label, show_value)):
            return Write(self, value)
        payload: dict[str, object] = {"value": value}
        if min is not UNSET:
            payload["min"] = min
        if max is not UNSET:
            payload["max"] = max
        if step is not UNSET:
            payload["step"] = step
        if label is not UNSET:
            payload["label"] = label
        if show_value is not UNSET:
            payload["show_value"] = show_value
        return Write(self, Dict.of(**payload))


class SwitchRef(InputLeaf):
    """On/off switch whose state lives in the browser."""

    _wire_type = "SwitchRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        value: bool = False,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            value=bool(value),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: BoolArg) -> Nu:
        return Write(self, value)


class TagInputRef(_Submits, _Placeholder, InputLeaf):
    """Multi-tag entry field whose committed list lives in the browser.

    Enter with text adds a tag (a change); Enter on an empty draft submits.
    """

    _wire_type = "TagInputRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        value: list[str] | None = None,
        max_tags: int | None = None,
        allow_duplicates: bool = False,
        clear_on_submit: bool = False,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            placeholder=placeholder,
            value=list(value or []),
            max_tags=max_tags,
            allow_duplicates=allow_duplicates,
            clear_on_submit=bool(clear_on_submit),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: ListArg[str]) -> Nu:
        return Write(self, value)


SubmitOn = Literal["mod+enter", "enter"]


class TextAreaRef(_Submits, _Placeholder, InputLeaf):
    """Multi-line text input whose value lives in the browser.

    Blur commits. cmd/ctrl+Enter commits and submits, plain Enter is a
    newline. `submit_on="enter"` makes it a chat composer: Enter submits and
    shift+Enter is the newline. Focus stays in the field after a submit, and
    `clear_on_submit` empties it for the next message.

    `auto_resize=True` maps to the primitive's `field-sizing: content` mode.
    Default face is display (Inter); `mono=True` flips `font-mono` at render
    for code-shaped fields.
    """

    _wire_type = "TextAreaRef"

    @classmethod
    def slot(
        cls,
        *,
        value: str = "",
        placeholder: str = "",
        rows: int = 4,
        max_length: int | None = None,
        auto_resize: bool = False,
        mono: bool = False,
        submit_on: SubmitOn = "mod+enter",
        clear_on_submit: bool = False,
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            value=value,
            placeholder=placeholder,
            rows=rows,
            max_length=max_length,
            auto_resize=auto_resize,
            mono=mono,
            submit_on=submit_on,
            clear_on_submit=bool(clear_on_submit),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)


class ToggleRef(InputLeaf):
    """Two-state toolbar button whose pressed state lives in the browser.

    Pressed or not is the value, read live like `SwitchRef`'s. `SwitchRef`
    stays the control for a setting; this is for a toolbar (bold, wrap, pin).
    `icon` takes the same lucide names as `ButtonRef.icon`, drawn before the
    label; with an empty label the icon name is the accessible name.
    """

    _wire_type = "ToggleRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        icon: str = "",
        value: bool = False,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            icon=icon,
            value=bool(value),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: BoolArg) -> Nu:
        return Write(self, value)

    def set_icon(self, name: StrArg) -> Nu:
        return Write(self, Dict.of(icon=name))


__all__ = [
    "CHANGE",
    "CLICK",
    "SUBMIT",
    "ButtonRef",
    "CheckboxRef",
    "CodeRef",
    "DatePickerRef",
    "InputLeaf",
    "InputRef",
    "MarkdownRef",
    "NumberInputRef",
    "RadioGroupRef",
    "SelectRef",
    "SketchRef",
    "SliderRef",
    "SwitchRef",
    "TagInputRef",
    "TextAreaRef",
    "ToggleRef",
]
