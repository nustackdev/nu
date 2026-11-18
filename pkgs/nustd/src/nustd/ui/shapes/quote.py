"""Quote Shape -- a header line over a body, set apart as quoted.

A Section over ``QuoteRef`` (``nustd.ui.refs.collections.quote``): the Ref
carries ``header``, ``set_title()``, the slot defaults and the wire type, and
``slot(**props)`` forwards to it.
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.collections.quote import QuoteRef


__all__ = ["Quote"]


class Quote(Section):
    """A header line over its slots, drawn as a quote. Props as ``QuoteRef.slot``.

    As a Shape, a slot named ``header`` is the header line::

        class Source(nustd.ui.Row):
            icon = nustd.ui.IconRef.slot(name="book-open")
            name = nustd.ui.TextRef.slot(value="RFC 9110", weight="medium")

        class Citation(nustd.ui.Quote):
            header = Source.slot()
            body = nustd.ui.TextRef.slot(value="A server MUST NOT ...")

        class Home(nustd.ui.Column):
            cite = Citation.slot()

    Refs alone, no Shape::

        note = QuoteRef("note", parent_ref=col, props={"title": "Note"})
        TextRef("t", parent_ref=note).set("Applies on the next deploy.")

        trace = QuoteRef("trace", parent_ref=col)
        TextRef("label", parent_ref=trace.header).set("Working")
        TextRef("when", parent_ref=trace.header).set("2m ago")
    """

    _ref_cls = QuoteRef
