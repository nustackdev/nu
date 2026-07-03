"""Modal: dialog overlay Section. Server controls open/closed; tab notifies on dismissal."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self

from nu import DictForm
from nu.domains.shape import Slot

from ..interactions.changed import Changed
from ..interactions.write import Write
from .section import Section, SectionRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["Modal", "ModalRef"]


class ModalRef(SectionRef):
    """SectionRef backing a Modal slot. Carries Modal-only interaction methods."""

    def store_open(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(open=flag))

    def store_title(self, text: Nu | str) -> Nu:
        return Write(self, DictForm.of(title=text))

    def store(self, open: Nu | bool | None = None, title: Nu | str | None = None) -> Nu:
        payload: dict[str, object] = {}
        if open is not None:
            payload["open"] = open
        if title is not None:
            payload["title"] = title
        return Write(self, DictForm.of(**payload))

    def changed(self) -> Changed:
        return Changed(self)


class Modal(Section):
    """Dialog overlay. Pin chrome on the subclass; declare body Refs as slots."""

    open: ClassVar[bool] = False
    title: ClassVar[str] = ""
    dismissible: ClassVar[bool] = True

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "open": cls.open,
            "title": cls.title,
            "dismissible": cls.dismissible,
        }

    @classmethod
    def slot(cls) -> Self:
        return Slot(ModalRef, section_cls=cls)  # type: ignore[return-value]
