"""Disclosure Shapes -- Collapsible, Popover and Sheet.

Each is a Section over its container Ref (``nustd.ui.refs.collections.disclosure``):
the Ref carries ``set()``, ``on_change()``, the slot defaults and the wire
type, and ``slot(**props)`` forwards to it. Declare the body as slots on a
subclass and drive open state off the bound Ref (``page.details.set(open=True)``).
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.collections.disclosure import CollapsibleRef, PopoverRef, SheetRef


__all__ = ["Collapsible", "Popover", "Sheet"]


class Collapsible(Section):
    """One titled region whose slots fold away. Props as ``CollapsibleRef.slot``.

    As a Shape::

        class Details(nustd.ui.Collapsible):
            hosts = HostsCard.slot()

        class Home(nustd.ui.Column):
            details = Details.slot(title="Details", open=True)

    Refs alone, no Shape::

        details = CollapsibleRef("details", parent_ref=col, props={"title": "Details"})
        TextRef("note", parent_ref=details).set("folded away")
    """

    _ref_cls = CollapsibleRef


class Popover(Section):
    """A button opening a floating panel of its slots. Props as ``PopoverRef.slot``.

    As a Shape::

        class Settings(nustd.ui.Popover):
            min = nustd.ui.NumberInputRef.slot(label="Min")

        class Home(nustd.ui.Column):
            settings = Settings.slot(icon="settings-2", tooltip="Settings")

    Refs alone, no Shape::

        pop = PopoverRef("settings", parent_ref=row, props={"icon": "settings-2"})
        TextRef("note", parent_ref=pop).set("tucked away")
    """

    _ref_cls = PopoverRef


class Sheet(Section):
    """Edge drawer with its slots as the body. Props as ``SheetRef.slot``.

    As a Shape::

        class Inspector(nustd.ui.Sheet):
            form = EditForm.slot()

        class Home(nustd.ui.Column):
            inspector = Inspector.slot(title="Edit host", side="right")

        Home.inspector.set(open=True)

    Refs alone, no Shape::

        sheet = SheetRef("inspector", parent_ref=col, props={"title": "Edit host"})
        TextRef("note", parent_ref=sheet).set("hello") >> sheet.set(open=True)
    """

    _ref_cls = SheetRef
