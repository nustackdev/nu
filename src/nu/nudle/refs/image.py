"""ImageRef: image by url with alt text and fit mode. Display-only."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from nu.queries.record import Record

from ..interactions.write import Write
from .base import NudleRef


if TYPE_CHECKING:
    from nu import Nu


__all__ = ["ImageRef"]


Fit = Literal["contain", "cover", "fill"]


class ImageRef(NudleRef):
    """Display-only image ref. One `write` op carries every mutation."""

    src: ClassVar[str] = ""
    alt: ClassVar[str] = ""
    fit: ClassVar[str] = "contain"
    width: ClassVar[int | None] = None
    height: ClassVar[int | None] = None
    rounded: ClassVar[bool] = False

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        out: dict[str, object] = {}
        if cls.src != "":
            out["src"] = cls.src
        if cls.alt != "":
            out["alt"] = cls.alt
        if cls.fit != "contain":
            out["fit"] = cls.fit
        if cls.width is not None:
            out["width"] = cls.width
        if cls.height is not None:
            out["height"] = cls.height
        if cls.rounded:
            out["rounded"] = cls.rounded
        return out

    def store_src(self, url: Nu | str) -> Nu:
        return Write(self, Record(src=url))

    def store_alt(self, text: Nu | str) -> Nu:
        return Write(self, Record(alt=text))

    def store_fit(self, mode: Nu | Fit | str) -> Nu:
        return Write(self, Record(fit=mode))

    def store_size(
        self,
        width: Nu | int | None,
        height: Nu | int | None,
    ) -> Nu:
        return Write(self, Record(width=width, height=height))

    def store_rounded(self, flag: Nu | bool) -> Nu:
        return Write(self, Record(rounded=flag))

    def store(
        self,
        src: Nu | str,
        alt: Nu | str | None = None,
        fit: Nu | Fit | str | None = None,
        width: Nu | int | None = None,
        height: Nu | int | None = None,
        rounded: Nu | bool | None = None,
    ) -> Nu:
        payload: dict[str, object] = {"src": src}
        if alt is not None:
            payload["alt"] = alt
        if fit is not None:
            payload["fit"] = fit
        if width is not None:
            payload["width"] = width
        if height is not None:
            payload["height"] = height
        if rounded is not None:
            payload["rounded"] = rounded
        return Write(self, Record(**payload))
