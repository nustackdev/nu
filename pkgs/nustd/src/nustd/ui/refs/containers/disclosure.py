"""Disclosure containers -- a region that opens and closes over its children.

STUBS, wired end to end so the disclosure unit only fills them in.

- ``CollapsibleRef``: one titled region that folds, simpler than Accordion.
- ``SheetRef``: an edge drawer, Modal's sibling for inspectors and side panels.

Open vs closed is the thing each one carries, so each will get a ``set()``
for it, the way Modal has one; that and the notify wiring are the unit's.
"""

from __future__ import annotations

from typing import Literal

from typing_extensions import Self

from .base import ContainerRef


__all__ = ["CollapsibleRef", "SheetRef"]


class CollapsibleRef(ContainerRef):
    """One titled region whose children fold away."""

    _wire_type = "Collapsible"

    @classmethod
    def slot(cls, *, title: str = "", open: bool = False) -> Self:
        return super().slot(title=title, open=bool(open))


Side = Literal["left", "right", "top", "bottom"]


class SheetRef(ContainerRef):
    """Drawer that slides in from an edge over the page, children as its body."""

    _wire_type = "Sheet"

    @classmethod
    def slot(cls, *, open: bool = False, title: str = "", side: Side = "right") -> Self:
        return super().slot(open=bool(open), title=title, side=side)
