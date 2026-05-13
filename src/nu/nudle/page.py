"""nudle.Page — Shape subclass tagged as a top-level UI page.

The only thing Page adds over Shape is a marker (so `serve` can pick it
out of a Nu tree) and a `.mount_fields()` helper that flattens the page's
slots into the `(path, wire_type)` list that ships in the `mount` frame.
"""

from __future__ import annotations

from typing import ClassVar

from nu.shapes.shape import Shape

from .refs import NudleRef


__all__ = ["Page"]


class Page(Shape):
    """Top-level UI page."""

    _is_nudle_page: ClassVar[bool] = True

    @classmethod
    def mount_fields(cls) -> list[tuple[str, str]]:
        """Flatten this page's nudle slots to `(path, wire_type)` pairs.

        v0.1.0 is flat — every slot is a top-level field. Nested page
        Shapes are not supported yet; when they are, this widens to
        dot-paths.
        """
        out: list[tuple[str, str]] = []
        for name, slot in cls._slots.items():
            ref_cls = slot.ref_cls
            if not issubclass(ref_cls, NudleRef):
                continue
            wire_type = ref_cls.wire_type
            if not wire_type:
                continue
            out.append((name, wire_type))
        return out
