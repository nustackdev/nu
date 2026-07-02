"""AccordionRef: stack of collapsible sections, each wrapping a child Ref. Section, not a Ref."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import DictForm

from ..interactions.changed import Changed
from ..interactions.write import Write
from .base import NudleRef
from .section import Section


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["AccordionRef"]


def _normalize_sections(items: object) -> list[dict[str, str]]:
    """Coerce a sections list to the canonical [{id, label}, ...] shape."""
    if not isinstance(items, list):
        return []
    out: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sid = item.get("id")
        label = item.get("label")
        out.append(
            {
                "id": "" if sid is None else str(sid),
                "label": "" if label is None else str(label),
            },
        )
    return out


def _normalize_open(ids: object) -> list[str]:
    if not isinstance(ids, list):
        return []
    return [str(x) for x in ids if x is not None]


class _AccordionMountRef(NudleRef):
    """Internal Ref bound to an AccordionRef subclass's mount point."""

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(address=None, owner_shape=section_cls)
        self._section_cls = section_cls

    async def aresolve_address(self, ctx: Context) -> str:
        mount = getattr(self._section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"AccordionRef {self._section_cls.__name__} has no mount point. "
                "Did you forget to declare it on a Page slot?",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class AccordionRef(Section):
    """Stack of collapsible sections. Tab owns open state, server owns the section list."""

    sections: ClassVar[list[dict[str, str]]] = []
    open: ClassVar[list[str]] = []
    multi: ClassVar[bool] = True

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "sections": _normalize_sections(cls.sections),
            "open": _normalize_open(cls.open),
            "multi": bool(cls.multi),
        }

    @classmethod
    def _mount_ref(cls) -> _AccordionMountRef:
        return _AccordionMountRef(section_cls=cls)

    @classmethod
    def store_sections(cls, items: Nu | list[dict[str, str]]) -> Nu:
        value = _normalize_sections(items) if isinstance(items, list) else items
        return Write(cls._mount_ref(), DictForm.of(sections=value))

    @classmethod
    def store_open(cls, ids: Nu | list[str]) -> Nu:
        value = _normalize_open(ids) if isinstance(ids, list) else ids
        return Write(cls._mount_ref(), DictForm.of(open=value))

    @classmethod
    def changed(cls) -> Changed:
        return Changed(cls._mount_ref())
