"""Input Refs -- tab-owned; server reads via `read` + `notify` path.

The browser owns the live value. Host reads via `Ref` (round-trip
through session), subscribes to changes via `.changed()` / `.clicked()`.
See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nu.ui.core import Changed, Ref, Write


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang import Nu
    from nu.lang.args import BoolArg, FloatArg, ListArg, StrArg
    from nu.lang.runtime import Runtime


Variant = Literal["primary", "secondary", "ghost", "danger"]


class ButtonRef(Ref):
    """Click trigger; subscribe via `.clicked()`."""

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        variant: Variant = "primary",
        disabled: bool = False,
        icon: str | None = None,
    ) -> Self:
        return super().slot(label=label, variant=variant, disabled=disabled, icon=icon)

    def clicked(self) -> Changed:
        return Changed(self)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_variant(self, name: Variant | StrArg) -> Nu:
        return Write(self, Dict.of(variant=name))

    def set_disabled(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(disabled=flag))

    def set(
        self,
        label: StrArg,
        variant: Variant | StrArg = UNSET,
        disabled: BoolArg = UNSET,
        icon: StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not UNSET:
            payload["variant"] = variant
        if disabled is not UNSET:
            payload["disabled"] = disabled
        if icon is not UNSET:
            payload["icon"] = icon
        return Write(self, Dict.of(**payload))


class CheckboxRef(Ref):
    """Boolean toggle whose checked state lives in the browser."""

    @classmethod
    def slot(cls, *, label: str = "", checked: bool = False) -> Self:
        return super().slot(label=label, checked=checked)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: BoolArg) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class DatePickerRef(Ref):
    """Date input whose ISO yyyy-mm-dd value lives in the browser."""

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        min: str = "",
        max: str = "",
        default: str = "",
    ) -> Self:
        return super().slot(
            label=label,
            placeholder=placeholder,
            min=min,
            max=max,
            default=default,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


InputType = Literal["text", "password", "email", "number"]


class InputRef(Ref):
    """Text input whose value lives in the browser.

    Default face is display (Inter); code-shaped fields opt into
    JetBrains Mono via `mono=True`, which flips `font-mono` at render time.
    """

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
    ) -> Self:
        return super().slot(
            label=label,
            placeholder=placeholder,
            value=value,
            type=type,
            max_length=max_length,
            mono=mono,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class NumberInputRef(Ref):
    """Numeric input whose value lives in the browser."""

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        min: float | None = None,
        max: float | None = None,
        step: float = 1.0,
        default: float = 0.0,
    ) -> Self:
        return super().slot(
            label=label,
            placeholder=placeholder,
            min=min,
            max=max,
            step=step,
            default=default,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set_value(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(value=value))

    def set_min(self, value: FloatArg | None) -> Nu:
        return Write(self, Dict.of(min=value))

    def set_max(self, value: FloatArg | None) -> Nu:
        return Write(self, Dict.of(max=value))

    def set_step(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(step=value))

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

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

    def changed(self) -> Changed:
        return Changed(self)


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


Orientation = Literal["vertical", "horizontal"]


class RadioGroupRef(Ref):
    """Single-choice radio group whose value lives in the browser."""

    @classmethod
    def slot(
        cls,
        *,
        options: list[str] | list[dict[str, str]] | None = None,
        selected: str = "",
        orientation: Orientation = "vertical",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            selected=selected,
            orientation=orientation,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        if isinstance(opts, list):
            payload: object = {"options": _normalize_options(opts)}
        else:
            payload = {"options": opts}
        return Write(self, Dict.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


OptionInput = "list[str] | list[dict[str, str]]"


class SelectRef(Ref):
    """Dropdown single-select whose value lives in the browser."""

    @classmethod
    def slot(
        cls,
        *,
        options: list[str] | list[dict[str, str]] | None = None,
        selected: str = "",
        placeholder: str = "",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            selected=selected,
            placeholder=placeholder,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        if isinstance(opts, list):
            payload: object = {"options": _normalize_options(opts)}
        else:
            payload = {"options": opts}
        return Write(self, Dict.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


class SliderRef(Ref):
    """Numeric slider whose value lives in the browser."""

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
    ) -> Self:
        return super().slot(
            min=min,
            max=max,
            step=step,
            value=value,
            label=label,
            show_value=show_value,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set_value(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(value=value))

    def set_min(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(min=value))

    def set_max(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(max=value))

    def set_step(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(step=value))

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

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

    def changed(self) -> Changed:
        return Changed(self)


class SwitchRef(Ref):
    """On/off switch whose checked state lives in the browser."""

    @classmethod
    def slot(cls, *, label: str = "", default: bool = False) -> Self:
        return super().slot(label=label, checked=default)

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: BoolArg) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class TagInputRef(Ref):
    """Multi-tag entry field whose committed list lives in the browser."""

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        value: list[str] | None = None,
        max_tags: int | None = None,
        allow_duplicates: bool = False,
    ) -> Self:
        return super().slot(
            label=label,
            placeholder=placeholder,
            value=list(value or []),
            max_tags=max_tags,
            allow_duplicates=allow_duplicates,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: ListArg[str]) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class TextAreaRef(Ref):
    """Multi-line text input whose value lives in the browser.

    `auto_resize=True` maps to the primitive's `field-sizing: content` mode.
    Default face is display (Inter); set `mono=True` at class level for
    code-shaped fields to flip `font-mono` at render.
    """

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
    ) -> Self:
        return super().slot(
            value=value,
            placeholder=placeholder,
            rows=rows,
            max_length=max_length,
            auto_resize=auto_resize,
            mono=mono,
        )

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def set(self, value: StrArg) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


__all__ = [
    "ButtonRef",
    "CheckboxRef",
    "DatePickerRef",
    "InputRef",
    "NumberInputRef",
    "RadioGroupRef",
    "SelectRef",
    "SliderRef",
    "SwitchRef",
    "TagInputRef",
    "TextAreaRef",
]
