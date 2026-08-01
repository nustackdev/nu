"""Section -- shape-based container primitive for the UI kit.

A Section is a Shape (not a Ref) that groups other Refs and Sections as
declared slots. Concrete layout primitives (Row, Column, Card, Tabs, ...)
subclass Section and pin chrome defaults; user code subclasses those.

Hosts stamp their own mount metadata onto a Section subclass at class
creation time (e.g. nudle's Page stamps `_nudle_mount`). This module
carries no host-specific markers.

SectionRef is the substrate Ref that backs a Section slot. Attribute
access on a bound SectionRef (e.g. `page.toolbar.text`) walks into the
section's child slots.
"""

from __future__ import annotations

from typing import Self

from nu import Shape
from nu.domains.shape import Slot

from .base import Ref


__all__ = ["Section", "SectionRef"]


class SectionRef(Ref):
    """Substrate Ref backing a Section slot.

    Instances are created by `Section.slot()` and exposed at the parent
    (Page or another Section) level. Carries `section_cls`; attribute
    access returns a child Ref whose `parent` is this SectionRef.
    """

    def __init__(
        self,
        address: object,
        *,
        section_cls: type[Section],
        parent_ref: Ref | None = None,
        owner_shape: type[Section] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape)
        self._payload["section_cls"] = section_cls

    def __getattr__(self, name: str) -> object:
        # Only called when normal attribute lookup fails. Map to a child
        # slot on the bound Section class. Read payload straight off __dict__
        # so this never recurses back through __getattr__.
        payload = self.__dict__.get("_payload") or {}
        section_cls = payload.get("section_cls")
        if section_cls is None:
            raise AttributeError(name)
        slots = getattr(section_cls, "_slots", {})
        if name in slots:
            slot = slots[name]
            return slot.create_ref(owner_shape=section_cls, parent_ref=self)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
            f" (section '{section_cls.__name__}' has no slot '{name}')"
        )


class Section(Shape):
    """Base for shape-based layout primitives.

    Subclass to declare child slots and pin chrome defaults:

        class Toolbar(Row):
            gap = 3
            text = TextRef.slot()
            btn = ButtonRef.slot()

    Hosts may stamp their own metadata onto Section subclasses (e.g.
    nudle's Page stamps mount-path info); this base carries none.
    """

    @classmethod
    def _mount_props(cls) -> dict[str, object]:
        """Class-level layout chrome shipped in the mount field entry."""
        return {}

    @classmethod
    def slot(cls) -> Self:
        return Slot(SectionRef, section_cls=cls)  # type: ignore[return-value]
