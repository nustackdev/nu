"""LinkRef: anchor with href, label, target, and an optional external indicator."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["LinkRef"]


Target = Literal["_self", "_blank"]

_UNSET: object = object()


class LinkRef(NudleRef):
    """Display-only link ref. One `write` op carries every mutation."""

    href: ClassVar[str] = ""
    label: ClassVar[str] = ""
    target: ClassVar[str] = "_self"
    external: ClassVar[bool | None] = None

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "href": cls.href,
            "label": cls.label,
            "target": cls.target,
            "external": cls.external,
        }

    def store_href(self, url: Nu | str) -> Nu:
        return Write(self, {"href": url})

    def store_label(self, text: Nu | str) -> Nu:
        return Write(self, {"label": text})

    def store_target(self, name: Nu | Target | str) -> Nu:
        return Write(self, {"target": name})

    def store_external(self, flag: Nu | bool | None) -> Nu:
        return Write(self, {"external": flag})

    def store(
        self,
        href: Nu | str | object = _UNSET,
        label: Nu | str | object = _UNSET,
        target: Nu | Target | str | object = _UNSET,
        external: Nu | bool | None | object = _UNSET,
    ) -> Nu:
        # Sentinel-based kwargs so callers can pass `external=None` (auto)
        # without conflating it with "do not touch this field".
        payload: dict[str, object] = {}
        if href is not _UNSET:
            payload["href"] = href
        if label is not _UNSET:
            payload["label"] = label
        if target is not _UNSET:
            payload["target"] = target
        if external is not _UNSET:
            payload["external"] = external
        return Write(self, payload)
