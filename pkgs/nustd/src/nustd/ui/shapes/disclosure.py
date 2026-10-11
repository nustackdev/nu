"""Disclosure Shapes -- Collapsible and Sheet. STUBS; the disclosure unit fills them in."""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.containers.disclosure import CollapsibleRef, SheetRef


__all__ = ["Collapsible", "Sheet"]


class Collapsible(Section):
    """One titled region whose slots fold away. Props as ``CollapsibleRef.slot``."""

    _ref_cls = CollapsibleRef


class Sheet(Section):
    """Edge drawer with its slots as the body. Props as ``SheetRef.slot``."""

    _ref_cls = SheetRef
