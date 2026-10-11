"""Section -- shape-based container primitive for the UI kit.

A Section is a Shape (not a Ref) that groups other Refs and Sections as
declared slots. It is layer 2, a declarative DSL over the container Refs:
the shipped Shapes (Row, Column, Card, Tabs, ...) each point ``_ref_cls``
at their container Ref, take their wire type from it, and forward slot
props to it. User code subclasses those.

A Section carries no mount point. It is a blueprint: the same subclass can
sit under as many parents as you like, and where it lands is decided by the
Ref chain that reaches it.

SectionRef is the substrate Ref under every container. Attribute access on
a bound SectionRef that carries a Section (e.g. ``page.toolbar.text``) walks
into the section's child slots. One built alone, with no Section, is still
a whole container: its children are Refs built with ``parent_ref=`` it.
Chrome a container can drive (Card's title, Tabs' active tab, ...) lives on
its Ref, so the write targets the bound Ref and resolves through the chain
like everything else.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self

from nu.domains.shape import Shape, Slot

from .base import Ref


if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["Section", "SectionRef"]


class SectionRef(Ref):
    """Substrate Ref under every container.

    Created by ``Section.slot()`` and exposed at the parent (Page or another
    Section) level, it carries ``section_cls`` and attribute access returns
    a child Ref whose ``parent`` is this SectionRef. ``section_cls`` is
    optional: a container Ref built alone has no Shape to navigate, and its
    children are built as Refs with ``parent_ref=`` it.
    """

    def __init__(
        self,
        address: object,
        *,
        section_cls: type[Section] | None = None,
        parent_ref: Ref | None = None,
        owner_shape: type[Section] | None = None,
        props: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(address, parent_ref=parent_ref, owner_shape=owner_shape, props=props)
        self._payload["section_cls"] = section_cls

    def __getattr__(self, name: str) -> object:
        # Only called when normal attribute lookup fails. Map to a child
        # slot on the bound Section class. Read payload straight off __dict__
        # so this never recurses back through __getattr__.
        payload = self.__dict__.get("_payload") or {}
        section_cls = payload.get("section_cls")
        if section_cls is None:
            if name.startswith("_"):
                raise AttributeError(name)
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
                " (it carries no Shape, so it has no slots to navigate; build"
                f" its children as Refs with parent_ref=)"
            )
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
            text = TextRef.slot()
            btn = ButtonRef.slot()

        bar = Toolbar.slot(gap=3)

    A Section subclass holds no mount point, so the same one can be
    declared on several pages at once.
    """

    # Container Ref backing this section's slot. Every shipped Shape points it
    # at its own (RowRef, CardRef, ...), which is where its chrome methods,
    # its slot defaults and its wire type live.
    _ref_cls: ClassVar[type[SectionRef]] = SectionRef

    # Browser component this Section renders as. Empty, the default, means
    # "whatever `_ref_cls` draws as", and failing that the class name; see
    # `_wire_type_of`. A Section that draws as its own browser node (nudle's
    # Page) declares it.
    _wire_type: ClassVar[str] = ""

    @classmethod
    def slot(cls, **props: object) -> Self:
        """Declare this Section as a slot. Props go to the Ref as they are.

        The Ref's own ``slot()`` normalizes them and fills its defaults, so a
        Shape and the Ref built alone (``RowRef("r", props=...)``) carry the
        same props.
        """
        declared = cls._ref_cls.slot(**props)
        return Slot(cls._ref_cls, props=dict(declared.props), section_cls=cls)  # type: ignore[return-value]
