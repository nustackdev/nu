"""Flow Shapes -- Column and Row, declared.

Each is a Section over its container Ref: ``_ref_cls`` names the Ref, the
wire type and the slot defaults come from it, and ``slot(**props)`` hands
the props over as they are.

    class Toolbar(Row):
        text = TextRef.slot()
        btn = ButtonRef.slot()

    bar = Toolbar.slot(gap=3, wrap=True)
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.containers.flow import ColumnRef, RowRef


__all__ = ["Column", "Row"]


class Column(Section):
    """Vertical stack of its slots. Props as ``ColumnRef.slot``."""

    _ref_cls = ColumnRef


class Row(Section):
    """Its slots side by side. Props as ``RowRef.slot``."""

    _ref_cls = RowRef
