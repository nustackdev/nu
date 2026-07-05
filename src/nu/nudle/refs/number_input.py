"""NumberInputRef: numeric input with min/max/step and stepper buttons. Browser is source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu import DictForm

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu import Nu
    from nu.lang.runtime import Runtime


__all__ = ["NumberInputRef"]


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
