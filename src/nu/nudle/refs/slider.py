"""SliderRef: numeric slider with min/max/step. Browser is source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["SliderRef"]


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

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store_value(self, value: Nu | float | int) -> Nu:
        return Write(self, {"value": value})

    def store_min(self, value: Nu | float | int) -> Nu:
        return Write(self, {"min": value})

    def store_max(self, value: Nu | float | int) -> Nu:
        return Write(self, {"max": value})

    def store_step(self, value: Nu | float | int) -> Nu:
        return Write(self, {"step": value})

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, {"label": text})

    def store_show_value(self, flag: Nu | bool) -> Nu:
        return Write(self, {"show_value": flag})

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
        return Write(self, payload)

    def changed(self) -> Changed:
        return Changed(self)
