"""InputGroup Shape -- a field and its buttons on one line, declared.

A Section over ``InputGroupRef``: ``class Search(InputGroup)`` with an
``InputRef`` slot and a ``ButtonRef`` slot draws the search box with its
button, and ``Search.slot()`` places it.
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.collections.input_group import InputGroupRef


__all__ = ["InputGroup"]


class InputGroup(Section):
    """A field and the buttons that act on it. Props as ``InputGroupRef.slot``."""

    _ref_cls = InputGroupRef
