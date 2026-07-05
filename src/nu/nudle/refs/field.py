"""FieldRef: labelled form-field wrapper. Section, not a Ref. Exactly one child slot."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from nu import DictForm

from ..interactions.write import Write
from .base import NudleRef
from .section import Section


if TYPE_CHECKING:
    from nu import Context, Nu


__all__ = ["FieldRef"]


class _FieldMountRef(NudleRef):
    """Internal Ref bound to a FieldRef subclass's mount point.

    Resolves directly via ``Section._nudle_mount`` so chrome writes (label,
    help, error, required) target the section's own wire path -- not the
    wrapped child.
    """

    def __init__(self, *, section_cls: type[Section]) -> None:
        super().__init__(address=None, owner_shape=section_cls)
        self._payload["section_cls"] = section_cls

    async def aresolve_address(self, ctx: Context) -> str:
        section_cls = self._payload.get("section_cls")
        mount = getattr(section_cls, "_nudle_mount", None)
        if mount is None:
            raise RuntimeError(
                f"FieldRef {section_cls.__name__} has no mount point. "
                "Did you forget to declare it on a Page slot?",
            )
        page_cls, slot_path = mount
        return ".".join([page_cls.__name__, *slot_path])


class FieldRef(Section):
    """Label + child input + help / error text. Exactly one child slot."""

    label: ClassVar[str] = ""
    help: ClassVar[str] = ""
    error: ClassVar[str] = ""
    required: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        slot_count = len(getattr(cls, "_slots", {}))
        if slot_count != 1:
            raise RuntimeError(
                f"FieldRef {cls.__name__} declares {slot_count} child slots; "
                "FieldRef requires exactly one.",
            )

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "label": cls.label,
            "help": cls.help,
            "error": cls.error,
            "required": cls.required,
        }

    @classmethod
    def _mount_ref(cls) -> _FieldMountRef:
        return _FieldMountRef(section_cls=cls)

    @classmethod
    def store_label(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(label=text))

    @classmethod
    def store_help(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(help=text))

    @classmethod
    def store_error(cls, text: Nu | str) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(error=text))

    @classmethod
    def store_required(cls, flag: Nu | bool) -> Nu:
        return Write(cls._mount_ref(), DictForm.of(required=flag))
