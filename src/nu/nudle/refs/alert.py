"""AlertRef: variant-tagged banner with title and body. Display, optionally dismissible."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu.queries.record import Record

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["AlertRef"]


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
        return Write(self, Record(variant=name))

    def store_title(self, text: Nu | str) -> Nu:
        return Write(self, Record(title=text))

    def store_body(self, text: Nu | str) -> Nu:
        return Write(self, Record(body=text))

    def store_dismissible(self, flag: Nu | bool) -> Nu:
        return Write(self, Record(dismissible=flag))

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
        return Write(self, Record(**payload))

    def dismissed(self) -> Changed:
        return Changed(self)
