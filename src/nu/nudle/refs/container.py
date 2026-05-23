"""Container: styled box Section. Wraps child slots with chrome.

A Container is a Shape (Section), not a Ref. Subclass it, declare
children as slots, mount as `panel = Panel.slot()`.

Example::

    class HeroCard(nudle.Container):
        title = "feature card"
        padding = "lg"
        background = "muted"
        border = "card"
        heading = nudle.HeadingRef.slot()
        body = nudle.TextRef.slot()
"""

from __future__ import annotations

from typing import ClassVar, Literal

from .section import Section


__all__ = ["Container"]


Padding = Literal["none", "sm", "md", "lg"]
Border = Literal["none", "hairline", "card"]
Background = Literal["none", "muted", "accent"]
Shadow = Literal["none", "sm", "md"]
Gap = Literal["none", "sm", "md", "lg"]


class Container(Section):
    """Styled card-like box. Pin chrome on the subclass."""

    title: ClassVar[str] = ""
    padding: ClassVar[str] = "md"
    border: ClassVar[str] = "hairline"
    background: ClassVar[str] = "none"
    shadow: ClassVar[str] = "none"
    gap: ClassVar[str] = "md"

    @classmethod
    def mount_props(cls) -> dict[str, object]:
        return {
            "title": cls.title,
            "padding": cls.padding,
            "border": cls.border,
            "background": cls.background,
            "shadow": cls.shadow,
            "gap": cls.gap,
        }
