"""Form: semantic <form> Section. Stacks child slots vertically; blocks page reload on Enter."""

from __future__ import annotations

from typing import ClassVar

from .section import Section


__all__ = ["Form"]


class Form(Section):
    """Semantic form wrapper. Pin chrome on the subclass; submit lives on a child ButtonRef."""

    title: ClassVar[str] = ""
    gap: ClassVar[int] = 4
    padding: ClassVar[int] = 0
    align: ClassVar[str] = "stretch"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "title": cls.title,
            "gap": cls.gap,
            "padding": cls.padding,
            "align": cls.align,
        }
