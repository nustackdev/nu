"""Line Shape -- slots that run inline, wrapping like a paragraph.

A Section over ``LineRef``: ``_ref_cls`` names the Ref, the wire type and
the slot defaults come from it, and ``slot(**props)`` hands the props over
as they are.

    class Status(Line):
        lead = TextRef.slot(value="press")
        combo = ShortcutRef.slot(keys=["mod", "K"])
        tail = TextRef.slot(value="to search")

    status = Status.slot(wrap=False)
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.collections.line import LineRef


__all__ = ["Line"]


class Line(Section):
    """Its slots inline, wrapping like a paragraph. Props as ``LineRef.slot``."""

    _ref_cls = LineRef
