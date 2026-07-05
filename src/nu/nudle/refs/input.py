"""Input Refs -- tab-owned; server reads via `read` + `notify` path.

The browser owns the live value. Host reads via `Ref` (round-trip
through session), subscribes to changes via `.changed()` / `.clicked()`.
See docs/nudle/interactions.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from nu import DictForm

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime


Variant = Literal["primary", "secondary", "ghost", "danger"]


class ButtonRef(NudleRef):
    """Click trigger; subscribe via `.clicked()`."""

    label: ClassVar[str] = ""
    variant: ClassVar[str] = "primary"
    disabled: ClassVar[bool] = False
    icon: ClassVar[str | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "variant": cls.variant,
            "disabled": cls.disabled,
            "icon": cls.icon,
        }

    def clicked(self) -> Changed:
        return Changed(self)

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_variant(self, name: Nu | Variant | str) -> Nu:
        return Write(self, DictForm.of(variant=name))

    def store_disabled(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(disabled=flag))

    def store(
        self,
        label: Nu | str,
        variant: Nu | Variant | str | None = None,
        disabled: Nu | bool | None = None,
        icon: Nu | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not None:
            payload["variant"] = variant
        if disabled is not None:
            payload["disabled"] = disabled
        if icon is not None:
            payload["icon"] = icon
        return Write(self, DictForm.of(**payload))


class CheckboxRef(NudleRef):
    """Boolean toggle whose checked state lives in the browser."""

    label: ClassVar[str] = ""
    checked: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "checked": cls.checked}

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | bool) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class DatePickerRef(NudleRef):
    """Date input whose ISO yyyy-mm-dd value lives in the browser."""

    label: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    min: ClassVar[str] = ""
    max: ClassVar[str] = ""
    default: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "placeholder": cls.placeholder,
            "min": cls.min,
            "max": cls.max,
            "default": cls.default,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


InputType = Literal["text", "password", "email", "number"]


class InputRef(NudleRef):
    """Text input whose value lives in the browser."""

    label: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    value: ClassVar[str] = ""
    type: ClassVar[str] = "text"
    max_length: ClassVar[int | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "placeholder": cls.placeholder,
            "value": cls.value,
            "type": cls.type,
            "max_length": cls.max_length,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class NumberInputRef(NudleRef):
    """Numeric input whose value lives in the browser."""

    label: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    min: ClassVar[float | None] = None
    max: ClassVar[float | None] = None
    step: ClassVar[float] = 1.0
    default: ClassVar[float] = 0.0

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "placeholder": cls.placeholder,
            "min": cls.min,
            "max": cls.max,
            "step": cls.step,
            "default": cls.default,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store_value(self, value: Nu | float | int) -> Nu:
        return Write(self, DictForm.of(value=value))

    def store_min(self, value: Nu | float | int | None) -> Nu:
        return Write(self, DictForm.of(min=value))

    def store_max(self, value: Nu | float | int | None) -> Nu:
        return Write(self, DictForm.of(max=value))

    def store_step(self, value: Nu | float | int) -> Nu:
        return Write(self, DictForm.of(step=value))

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store(
        self,
        value: Nu | float | int,
        min: Nu | float | int | None = None,
        max: Nu | float | int | None = None,
        step: Nu | float | int | None = None,
        label: Nu | str | None = None,
    ) -> Nu:
        # Scalar shortcut: just the number when no extra kwargs are passed.
        if min is None and max is None and step is None and label is None:
            return Write(self, value)
        payload: dict[str, object] = {"value": value}
        if min is not None:
            payload["min"] = min
        if max is not None:
            payload["max"] = max
        if step is not None:
            payload["step"] = step
        if label is not None:
            payload["label"] = label
        return Write(self, DictForm.of(**payload))

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


class RadioGroupRef(NudleRef):
    """Single-choice radio group whose value lives in the browser."""

    options: ClassVar[list[Any]] = []
    selected: ClassVar[str] = ""
    orientation: ClassVar[str] = "vertical"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "options": _normalize_options(cls.options),
            "selected": cls.selected,
            "orientation": cls.orientation,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def store_options(self, opts: Nu | list[str] | list[dict[str, str]]) -> Nu:
        if isinstance(opts, list):
            payload: object = {"options": _normalize_options(opts)}
        else:
            payload = {"options": opts}
        return Write(self, DictForm.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


OptionInput = "list[str] | list[dict[str, str]]"


class SelectRef(NudleRef):
    """Dropdown single-select whose value lives in the browser."""

    options: ClassVar[list[Any]] = []
    selected: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "options": _normalize_options(cls.options),
            "selected": cls.selected,
            "placeholder": cls.placeholder,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | str) -> Nu:
        return Write(self, value)

    def store_options(self, opts: Nu | list[str] | list[dict[str, str]]) -> Nu:
        if isinstance(opts, list):
            payload: object = {"options": _normalize_options(opts)}
        else:
            payload = {"options": opts}
        return Write(self, DictForm.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


class SliderRef(NudleRef):
    """Numeric slider whose value lives in the browser."""

    min: ClassVar[float] = 0.0
    max: ClassVar[float] = 100.0
    step: ClassVar[float] = 1.0
    value: ClassVar[float] = 0.0
    label: ClassVar[str] = ""
    show_value: ClassVar[bool] = True

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "min": cls.min,
            "max": cls.max,
            "step": cls.step,
            "value": cls.value,
            "label": cls.label,
            "show_value": cls.show_value,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store_value(self, value: Nu | float | int) -> Nu:
        return Write(self, DictForm.of(value=value))

    def store_min(self, value: Nu | float | int) -> Nu:
        return Write(self, DictForm.of(min=value))

    def store_max(self, value: Nu | float | int) -> Nu:
        return Write(self, DictForm.of(max=value))

    def store_step(self, value: Nu | float | int) -> Nu:
        return Write(self, DictForm.of(step=value))

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(label=text))

    def store_show_value(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(show_value=flag))

    def store(
        self,
        value: Nu | float | int,
        min: Nu | float | int | None = None,
        max: Nu | float | int | None = None,
        step: Nu | float | int | None = None,
        label: Nu | str | None = None,
        show_value: Nu | bool | None = None,
    ) -> Nu:
        # Scalar shortcut: just the number when no extra kwargs are passed.
        if min is None and max is None and step is None and label is None and show_value is None:
            return Write(self, value)
        payload: dict[str, object] = {"value": value}
        if min is not None:
            payload["min"] = min
        if max is not None:
            payload["max"] = max
        if step is not None:
            payload["step"] = step
        if label is not None:
            payload["label"] = label
        if show_value is not None:
            payload["show_value"] = show_value
        return Write(self, DictForm.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


class SwitchRef(NudleRef):
    """On/off switch whose checked state lives in the browser."""

    label: ClassVar[str] = ""
    default: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "checked": cls.default}

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | bool) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class TagInputRef(NudleRef):
    """Multi-tag entry field whose committed list lives in the browser."""

    label: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    value: ClassVar[list[str]] = []
    max_tags: ClassVar[int | None] = None
    allow_duplicates: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "placeholder": cls.placeholder,
            "value": list(cls.value),
            "max_tags": cls.max_tags,
            "allow_duplicates": cls.allow_duplicates,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | list[str]) -> Nu:
        return Write(self, value)

    def changed(self) -> Changed:
        return Changed(self)


class TextAreaRef(NudleRef):
    """Multi-line text input whose value lives in the browser."""

    value: ClassVar[str] = ""
    placeholder: ClassVar[str] = ""
    rows: ClassVar[int] = 4
    max_length: ClassVar[int | None] = None
    auto_resize: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "placeholder": cls.placeholder,
            "rows": cls.rows,
            "max_length": cls.max_length,
            "auto_resize": cls.auto_resize,
        }

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> Any:
            return await self._aread(rt, nid)

        return athunk

    def store(self, value: Nu | str) -> Nu:
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
