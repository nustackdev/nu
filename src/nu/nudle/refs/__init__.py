"""nudle Refs and Sections.

Three kinds of Refs:
- Display Refs (body): render into the visible tree. BadgeRef, ButtonRef,
  CheckboxRef, HeadingRef, ImageRef, InputRef, JsonViewerRef, LineChart,
  LinkRef, MarkdownRef, ProgressRef, SelectRef, SliderRef, TableRef,
  TextAreaRef, TextRef.
- Structural Refs (Index-level): bound to non-store browser APIs.
  TitleRef (document.title), NavRef (history+location).

Layout primitives are Sections (Shape-based), not Refs:
- Row, Column, Container -- live in this package and are exported here
  so the wire-type resolver (`_wire_type`) finds them via MRO.
"""

from __future__ import annotations

from .badge import BadgeRef
from .base import NudleRef
from .button import ButtonRef
from .checkbox import CheckboxRef
from .column import Column
from .container import Container
from .heading import HeadingRef
from .image import ImageRef
from .input import InputRef
from .json_viewer import JsonViewerRef
from .line_chart import LineChart
from .link import LinkRef
from .markdown import MarkdownRef
from .nav import NavRef
from .progress import ProgressRef
from .row import Row
from .section import Section
from .select import SelectRef
from .slider import SliderRef
from .table import TableRef
from .text import TextRef
from .text_area import TextAreaRef
from .title import TitleRef


__all__ = [
    "BadgeRef",
    "ButtonRef",
    "CheckboxRef",
    "Column",
    "Container",
    "HeadingRef",
    "ImageRef",
    "InputRef",
    "JsonViewerRef",
    "LineChart",
    "LinkRef",
    "MarkdownRef",
    "NavRef",
    "NudleRef",
    "ProgressRef",
    "Row",
    "Section",
    "SelectRef",
    "SliderRef",
    "TableRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
]
