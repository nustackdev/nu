"""GaugeRef: circular dial showing a ratio in [0, 1] with optional caption. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import DictForm

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["GaugeRef"]


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
