"""Shapes: layer 2, a declarative DSL over the container Refs.

A Shape is a ``Section`` subclass with ``_ref_cls`` set to its container Ref.
Everything that decides what reaches the browser lives on that Ref: the slot
props and their defaults (``Section.slot`` only forwards), the chrome methods
on the bound Ref, and the wire type (``class Toolbar(Row)`` draws as ``Row``
because ``RowRef`` does). A Shape adds one thing, named child slots, so a
subclass reads as the tree it draws.

Anything a Shape declares can also be built from Refs alone; see
``nustd.ui.refs``. Modules here import from ``nustd.ui.refs.containers`` and
``nustd.ui.core`` only, never from the ``nustd.ui.refs`` package root.

- flow:   Column, Row.
- grid:   Grid, equal cells.
- line:   Line, slots that run inline.
- chrome: Card, Box, Tabs, Modal, Accordion, Form, Fieldset, Field.
- disclosure: Collapsible, Sheet.
- list:   List, one item per slot.
- page:   PageSection, NavList.
"""

from __future__ import annotations

from .chrome import Accordion, Box, Card, Field, Fieldset, Form, Modal, Tabs
from .disclosure import Collapsible, Sheet
from .flow import Column, Row
from .grid import Grid
from .line import Line
from .list import List
from .page import NavList, PageSection


__all__ = [
    "Accordion",
    "Box",
    "Card",
    "Collapsible",
    "Column",
    "Field",
    "Fieldset",
    "Form",
    "Grid",
    "Line",
    "List",
    "Modal",
    "NavList",
    "PageSection",
    "Row",
    "Sheet",
    "Tabs",
]
