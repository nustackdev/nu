"""List Shape -- a list whose slots are its items.

    class Links(List):
        docs = LinkRef.slot(label="Docs", href="/docs")
        status = BadgeRef.slot(label="live", variant="ok")

    links = Links.slot(variant="number")

Each declared slot is one item, after any plain strings in ``items``. Props,
chrome and the wire type come from ``ListRef``.
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.containers.list import ListRef


__all__ = ["List"]


class List(Section):
    """Bulleted or numbered list, one item per slot. Props as ``ListRef.slot``."""

    _ref_cls = ListRef
