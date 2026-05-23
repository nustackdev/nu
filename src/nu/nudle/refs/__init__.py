"""nudle Refs and Sections.

Three kinds of Refs:
- Display Refs (body): render into the visible tree. AreaChart, BadgeRef,
  BarChart, ButtonRef, CheckboxRef, GaugeRef, HeadingRef, ImageRef, InputRef,
  JsonViewerRef, LineChart, LinkRef, MarkdownRef, PieChart, ProgressRef,
  SelectRef, SliderRef, Sparkline, TableRef, TextAreaRef, TextRef.
- Structural Refs (Index-level): bound to non-store browser APIs.
  TitleRef (document.title), NavRef (history+location).

Layout primitives are Sections (Shape-based), not Refs:
- Row, Column, Container -- live in this package and are exported here
  so the wire-type resolver (`_wire_type`) finds them via MRO.
"""

from __future__ import annotations

from .accordion import AccordionRef
from .alert import AlertRef
from .area_chart import AreaChart
from .badge import BadgeRef
from .bar_chart import BarChart
from .base import NudleRef
from .button import ButtonRef
from .card import CardRef
from .checkbox import CheckboxRef
from .code_block import CodeBlockRef
from .column import Column
from .container import Container
from .date_picker import DatePickerRef
from .divider import DividerRef
from .field import FieldRef
from .fieldset import Fieldset
from .form import Form
from .gauge import GaugeRef
from .heading import HeadingRef
from .image import ImageRef
from .input import InputRef
from .json_viewer import JsonViewerRef
from .line_chart import LineChart
from .link import LinkRef
from .markdown import MarkdownRef
from .modal import Modal
from .nav import NavRef
from .number_input import NumberInputRef
from .pie_chart import PieChart
from .progress import ProgressRef
from .radio_group import RadioGroupRef
from .row import Row
from .section import Section
from .select import SelectRef
from .slider import SliderRef
from .sparkline import Sparkline
from .stat import StatRef
from .switch import SwitchRef
from .table import TableRef
from .tabs import TabsRef
from .tag_input import TagInputRef
from .text import TextRef
from .text_area import TextAreaRef
from .title import TitleRef


__all__ = [
    "AccordionRef",
    "AlertRef",
    "AreaChart",
    "BadgeRef",
    "BarChart",
    "ButtonRef",
    "CardRef",
    "CheckboxRef",
    "CodeBlockRef",
    "Column",
    "Container",
    "DatePickerRef",
    "DividerRef",
    "FieldRef",
    "Fieldset",
    "Form",
    "GaugeRef",
    "HeadingRef",
    "ImageRef",
    "InputRef",
    "JsonViewerRef",
    "LineChart",
    "LinkRef",
    "MarkdownRef",
    "Modal",
    "NavRef",
    "NudleRef",
    "NumberInputRef",
    "PieChart",
    "ProgressRef",
    "RadioGroupRef",
    "Row",
    "Section",
    "SelectRef",
    "SliderRef",
    "Sparkline",
    "StatRef",
    "SwitchRef",
    "TableRef",
    "TabsRef",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
]
