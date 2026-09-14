"""Section -- shape-based container primitive for the UI kit.

A Section is a Shape (not a Ref) that groups other Refs and Sections as
declared slots. Concrete layout primitives (Row, Column, Card, Tabs, ...)
subclass Section and pin chrome defaults; user code subclasses those.

A Section carries no mount point. It is a blueprint: the same subclass can
sit under as many parents as you like, and where it lands is decided by the
Ref chain that reaches it.

SectionRef is the substrate Ref that backs a Section slot. Attribute
access on a bound SectionRef (e.g. `page.toolbar.text`) walks into the
section's child slots. A Section whose own chrome is drivable (Card's
title, Tabs' active tab, ...) points `_ref_cls` at a SectionRef subclass
carrying those methods, so the write targets the bound Ref and resolves
through the chain like everything else.
"""

from __future__ import annotations

from typing import ClassVar

from typing_extensions import Self

from nu.domains.shape import Shape, Slot

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

    A Section subclass holds no mount point, so the same one can be
    declared on several pages at once.
    """

    # SectionRef subclass backing this section's slot. Override to hand the
    # bound Ref section-specific chrome methods (see ModalRef, CardRef).
    _ref_cls: ClassVar[type[SectionRef]] = SectionRef

    @classmethod
    def slot(cls, **props: object) -> Self:
        return Slot(cls._ref_cls, props=props, section_cls=cls)  # type: ignore[return-value]
