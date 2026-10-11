"""Chrome Shapes -- Card, Container, Tabs, Modal, Accordion, Form, Fieldset, Field.

Each is a Section over its container Ref (``nustd.ui.refs.containers.chrome``):
the Ref carries the chrome methods, the slot defaults and the wire type, and
``slot(**props)`` forwards to it. Declare the body as slots on a subclass and
drive the chrome off the bound Ref (``page.card.set_title(...)``).
"""

from __future__ import annotations

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


__all__ = ["Accordion", "Card", "Container", "Field", "Fieldset", "Form", "Modal", "Tabs"]


class Accordion(Section):
    """Stack of collapsible sections. Tab owns open state, server owns the section list."""

    _ref_cls = AccordionRef


class Card(Section):
    """Card-styled Section: title + subtitle + body slots + footer."""

    _ref_cls = CardRef


class Container(Section):
    """Styled card-like box. Pin chrome on slot()."""

    _ref_cls = BoxRef


class Field(Section):
    """Label + child input + help / error text. Exactly one child slot."""

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
    """Grouped fields with a legend. Display-only, server-owned."""

    _ref_cls = FieldsetRef


class Form(Section):
    """Semantic form wrapper. Pin chrome on slot(); submit lives on a child ButtonRef."""

    _ref_cls = FormRef


class Modal(Section):
    """Dialog overlay. Pin chrome on slot(); declare body Refs as slots."""

    _ref_cls = ModalRef


class Tabs(Section):
    """Tab strip plus active body. Subclass and declare one child slot per tab body."""

    _ref_cls = TabsRef
