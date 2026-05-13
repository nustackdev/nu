"""nudle.Page -- Shape subclass tagged as a top-level UI page.

The only delta over Shape is a marker (so `serve` can pick it out of a
Nu tree) and `mount_fields()` which flattens nudle slots into the list
of `{"path", "type"}` dicts shipped in the `mount` frame. The wire
type for each field is the Ref class name verbatim.
"""

from __future__ import annotations

from typing import ClassVar

from nu.shapes.shape import Shape

from .refs.base import NudleRef


__all__ = ["Page"]


class Page(Shape):
    """Top-level UI page."""

    _is_nudle_page: ClassVar[bool] = True

    @classmethod
    def mount_fields(cls) -> list[dict[str, str]]:
        """Flatten this page's nudle slots into `{path, type}` dicts."""
        out: list[dict[str, str]] = []
        for name, slot in cls._slots.items():
            ref_cls = slot.ref_cls
            if not issubclass(ref_cls, NudleRef):
                continue
            out.append({"path": name, "type": ref_cls.__name__})
        return out
