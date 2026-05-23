"""NumberInputRef: numeric input with min/max/step and stepper buttons. Browser is source of truth."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from nu.queries.record import Record

from ..interactions.changed import Changed
from ..interactions.write import Write
from ..session import NudleSession
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Context, Nu


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

    async def aeval(self, ctx: Context) -> Any:
        session = ctx.get(NudleSession)
        path = await self.aresolve_address(ctx)
        return await session.aread(path)

    def store_value(self, value: Nu | float | int) -> Nu:
        return Write(self, Record(value=value))

    def store_min(self, value: Nu | float | int | None) -> Nu:
        return Write(self, Record(min=value))

    def store_max(self, value: Nu | float | int | None) -> Nu:
        return Write(self, Record(max=value))

    def store_step(self, value: Nu | float | int) -> Nu:
        return Write(self, Record(step=value))

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, Record(label=text))

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
        return Write(self, Record(**payload))

    def changed(self) -> Changed:
        return Changed(self)
