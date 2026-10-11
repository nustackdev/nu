"""``LeafRef`` -- the base every content, input and collection Ref builds on.

Layer 1. A leaf draws one thing from its own props: a text, a button, a
chart, a table. Its fixed known parts are props (a button's ``label`` and
``icon``), never child nodes, and it never has children: building a Ref with
``parent_ref=`` a leaf raises ``TypeError`` and names a container to use.
Composition is what containers are for.
"""

from __future__ import annotations

from typing import ClassVar

from nustd.ui.core import Ref


__all__ = ["LeafRef"]


class LeafRef(Ref):
    """Base for leaf Refs: one thing drawn from props, no children. Abstract."""

    _leaf: ClassVar[bool] = True

    # Abstract: never on the wire. Every concrete leaf declares its own.
    _wire_type: ClassVar[str] = ""
