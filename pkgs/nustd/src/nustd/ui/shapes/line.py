"""Line Shape -- slots that run inline. STUB over ``LineRef``; the line unit fills it in."""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.containers.line import LineRef


__all__ = ["Line"]


class Line(Section):
    """Its slots inline, wrapping like a paragraph. Props as ``LineRef.slot``."""

    _ref_cls = LineRef
