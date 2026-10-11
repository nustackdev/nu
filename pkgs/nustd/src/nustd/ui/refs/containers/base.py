"""``ContainerRef`` -- the base every layout container Ref builds on.

Layer 1. A container Ref is a whole container on its own: it needs no Shape
to draw, to carry chrome or to hold children.

- **Children** come from ``parent_ref=``: ``TextRef("t", parent_ref=row)``
  puts a text in ``row``. Navigating a Shape whose ``_ref_cls`` is this Ref
  (``page.toolbar.text``) reaches the same place by way of its slots.
- **Repetition is free.** The address is a term, so computed keys under one
  parent (``RowRef(nu.Str("r") + nu.str(i), parent_ref=col)``) are as many
  distinct children as there are keys, with nothing declared up front.
- **Props** ride ``props=`` on the constructor, or ``slot(**props)`` when the
  Ref is declared on a Shape; both go through this class's own ``slot()``,
  so the defaults and normalization live here and nowhere else.
- **No ``set()``** unless one chrome value is the thing the container
  carries (Modal: open). The rest of its chrome is ``set_*``. ``ListRef``
  keeps its old string ``set(items)`` for compatibility.

The parent's flow decides how a child displays: the same Badge is a block in
a Column, a cell in a Grid and a run of text in a Line. A child never says.
"""

from __future__ import annotations

from typing import ClassVar

from nustd.ui.core import SectionRef


__all__ = ["ContainerRef"]


class ContainerRef(SectionRef):
    """Base for container Refs: open-ended children, optional chrome. Abstract.

    Something is a container only when its children are open-ended user
    composition. Fixed known parts (a button's label and icon) are props on
    a leaf instead.
    """

    # Abstract: never on the wire. Every concrete container declares its own.
    _wire_type: ClassVar[str] = ""
