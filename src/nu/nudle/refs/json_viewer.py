"""JsonViewerRef: collapsible json tree viewer. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu import DictForm

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["JsonViewerRef"]


Theme = Literal["light", "dark"]


class JsonViewerRef(NudleRef):
    """Display-only json viewer ref. One `write` op carries every mutation via partial-merge."""

    value: ClassVar[object] = None
    expand_depth: ClassVar[int] = 1
    theme: ClassVar[str] = "light"
    copyable: ClassVar[bool] = False
    sortable: ClassVar[bool] = False
    max_height: ClassVar[int | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "value": cls.value,
            "expand_depth": cls.expand_depth,
            "theme": cls.theme,
            "copyable": cls.copyable,
            "sortable": cls.sortable,
            "max_height": cls.max_height,
        }

    def store_value(self, value: Nu | object) -> Nu:
        return Write(self, DictForm.of(value=value))

    def store_expand_depth(self, depth: Nu | int) -> Nu:
        return Write(self, DictForm.of(expand_depth=depth))

    def store_theme(self, name: Nu | Theme | str) -> Nu:
        return Write(self, DictForm.of(theme=name))

    def store_copyable(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(copyable=flag))

    def store_sortable(self, flag: Nu | bool) -> Nu:
        return Write(self, DictForm.of(sortable=flag))

    def store_max_height(self, px: Nu | int | None) -> Nu:
        return Write(self, DictForm.of(max_height=px))

    def store(
        self,
        value: Nu | object,
        expand_depth: Nu | int | None = None,
        theme: Nu | Theme | str | None = None,
        copyable: Nu | bool | None = None,
        sortable: Nu | bool | None = None,
        max_height: Nu | int | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"value": value}
        if expand_depth is not None:
            payload["expand_depth"] = expand_depth
        if theme is not None:
            payload["theme"] = theme
        if copyable is not None:
            payload["copyable"] = copyable
        if sortable is not None:
            payload["sortable"] = sortable
        if max_height is not None:
            payload["max_height"] = max_height
        return Write(self, DictForm.of(**payload))
