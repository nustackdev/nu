"""nudle Refs. One module per Ref type.

Two kinds:
- Display Refs (body): IntRef, LineChart, HeadingRef, TableRef, ButtonRef, InputRef.
  Backed by a store slice on the browser; render into the visible tree.
- Structural Refs (Index-level): TitleRef (document.title), NavRef (history+location).
  Bound to browser APIs other than the render store; not rendered.
"""

from __future__ import annotations

from .badge import BadgeRef
from .base import NudleRef
from .button import ButtonRef
from .heading import HeadingRef
from .input import InputRef
from .int_ import IntRef
from .line_chart import LineChart
from .nav import NavRef
from .table import TableRef
from .title import TitleRef


__all__ = [
    "BadgeRef",
    "ButtonRef",
    "HeadingRef",
    "InputRef",
    "IntRef",
    "LineChart",
    "NavRef",
    "NudleRef",
    "TableRef",
    "TitleRef",
]
