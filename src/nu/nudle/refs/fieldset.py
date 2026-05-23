"""Fieldset: grouped fields with a legend and shared vertical spacing. Section, not a Ref."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu.queries.record import Record

from ..interactions.write import Write
from .base import NudleRef
from .section import Section


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["Fieldset"]


Gap = Literal["sm", "md", "lg"]


class _FieldsetMountRef(NudleRef):
    """Internal Ref bound to a Fieldset subclass's mount point.

    Resolves directly via ``Section._nudle_mount`` so chrome writes (legend,
    gap, disabled) target the section's own wire path -- not a child.
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(address=None, owner_shape=section_cls)
        self._section_cls = section_cls

    async def aresolve_address(self, ctx: Context) -> str:
        mount = getattr(self._section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"Fieldset {self._section_cls.__name__} has no mount point. "
                "Did you forget to declare it on a Page slot?",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class Fieldset(Section):
    """Grouped fields with a legend. Display-only, server-owned."""

    legend: ClassVar[str] = ""
    gap: ClassVar[str] = "md"
    disabled: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {"legend": cls.legend, "gap": cls.gap, "disabled": cls.disabled}

    @classmethod
    def _mount_ref(cls) -> _FieldsetMountRef:
        return _FieldsetMountRef(section_cls=cls)

    @classmethod
    def store_legend(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), Record(legend=text))

    @classmethod
    def store_gap(cls, value: Nu | Gap | str) -> Nu:
        return Write(cls._mount_ref(), Record(gap=value))

    @classmethod
    def store_disabled(cls, flag: Nu | bool) -> Nu:
        return Write(cls._mount_ref(), Record(disabled=flag))
