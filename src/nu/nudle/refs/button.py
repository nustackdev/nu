"""ButtonRef: click trigger. No value, just notifications."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu.queries.record import Record

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["ButtonRef"]


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
        return Write(self, Record(label=text))

    def store_variant(self, name: Nu | Variant | str) -> Nu:
        return Write(self, Record(variant=name))

    def store_disabled(self, flag: Nu | bool) -> Nu:
        return Write(self, Record(disabled=flag))

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
        return Write(self, Record(**payload))
