"""BadgeRef: small label with a variant tag. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu.queries.record import Record

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["BadgeRef"]


Variant = Literal["info", "warn", "ok", "danger", "neutral"]


class BadgeRef(NudleRef):
    """Display-only badge ref. One `write` op carries every mutation."""

    label: ClassVar[str] = ""
    variant: ClassVar[str] = "neutral"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"label": cls.label, "variant": cls.variant}

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, Record(label=text))

    def store_variant(self, name: Nu | Variant | str) -> Nu:
        return Write(self, Record(variant=name))

    def store(
        self,
        label: Nu | str,
        variant: Nu | Variant | str | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"label": label}
        if variant is not None:
            payload["variant"] = variant
        return Write(self, Record(**payload))
