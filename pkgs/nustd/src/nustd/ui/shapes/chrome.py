"""Chrome Shapes -- Card, Box, Tabs, Modal, Accordion, Form, Fieldset, Field.

Each is a Section over its container Ref (``nustd.ui.refs.containers.chrome``):
the Ref carries the chrome methods, the slot defaults and the wire type, and
``slot(**props)`` forwards to it. Declare the body as slots on a subclass and
drive the chrome off the bound Ref (``page.card.set_title(...)``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nustd.ui.core import Section
from nustd.ui.refs.containers.chrome import (
    AccordionRef,
    BoxRef,
    CardRef,
    FieldRef,
    FieldsetRef,
    FormRef,
    ModalRef,
    TabsRef,
)


if TYPE_CHECKING:
    from nustd.ui.core import Ref


__all__ = ["Accordion", "Box", "Card", "Field", "Fieldset", "Form", "Modal", "Tabs"]


def _strip(shape: type[Section], given: object, prop: str) -> object:
    """The ``tabs`` / ``sections`` list a Tabs or Accordion Shape declares, checked.

    Each declared slot is the body of the entry with its name as id, and an
    entry is the only thing that draws a body. So an empty list is derived
    from the slots, one entry per slot in declaration order, labelled by its
    name; and a list that leaves a slot out raises, since that slot would
    never show. Entries naming no slot are fine: they are item template
    children, ``tabs[id]``.
    """
    slots = list(getattr(shape, "_slots", {}))
    if not given:
        return [{"id": name, "label": name.replace("_", " ").capitalize()} for name in slots]
    if isinstance(given, list):
        listed = {str(e.get("id")) for e in given if isinstance(e, dict)}
        missing = [name for name in slots if name not in listed]
        if missing:
            msg = (
                f"{shape.__name__} declares slot(s) {missing} that {prop}= does not list, so they"
                f" would never draw; add an entry for each, or leave {prop}= out to take them all"
            )
            raise ValueError(msg)
    return given


class Accordion(Section):
    """Collapsible sections, one per slot. Props as ``AccordionRef.slot``.

    A slot is the body of the section whose id is its name. ``sections=`` left
    out lists every slot in declaration order; given, it must list them all.
    """

    _ref_cls = AccordionRef

    @classmethod
    def slot(cls, item: type[Section] | type[Ref] | None = None, /, **props: object) -> Self:
        """Declare it as a slot, ``sections=`` derived from the slots when left out."""
        props["sections"] = _strip(cls, props.get("sections"), "sections")
        return super().slot(item, **props)


class Card(Section):
    """Card-styled box around its slots. Props as ``CardRef.slot``.

    Slots named ``media``, ``actions`` and ``footer`` draw in the card's own
    places (top, header rail, bottom edge) instead of the body; ``card.media``,
    ``card.actions`` and ``card.footer`` reach them. ``caption=`` is a line of
    text along the bottom.
    """

    _ref_cls = CardRef


class Box(Section):
    """Styled box around its slots. Props as ``BoxRef.slot``."""

    _ref_cls = BoxRef


class Field(Section):
    """Label, exactly one child input slot, help and error. Props as ``FieldRef.slot``."""

    _ref_cls = FieldRef

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        slot_count = len(getattr(cls, "_slots", {}))
        if slot_count != 1:
            raise RuntimeError(
                f"Field {cls.__name__} declares {slot_count} child slots; "
                "Field requires exactly one.",
            )


class Fieldset(Section):
    """Its slots grouped under a legend. Props as ``FieldsetRef.slot``."""

    _ref_cls = FieldsetRef


class Form(Section):
    """Its slots in a semantic form; submit is a child ButtonRef. Props as ``FormRef.slot``."""

    _ref_cls = FormRef


class Modal(Section):
    """Dialog overlay with its slots as the body. Props as ``ModalRef.slot``."""

    _ref_cls = ModalRef


class Tabs(Section):
    """Tab strip, one tab per slot, the active one's body shown. Props as ``TabsRef.slot``.

    A slot is the body of the tab whose id is its name; ``tabs[id]`` with an
    item template is one too. ``tabs=`` left out lists every slot in
    declaration order; given, it must list them all.
    """

    _ref_cls = TabsRef

    @classmethod
    def slot(cls, item: type[Section] | type[Ref] | None = None, /, **props: object) -> Self:
        """Declare it as a slot, ``tabs=`` derived from the slots when left out."""
        props["tabs"] = _strip(cls, props.get("tabs"), "tabs")
        return super().slot(item, **props)
