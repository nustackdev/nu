"""nudle Refs and Sections.

Grouped by kind, one module per group. See docs/nudle/interactions.md.

- structural: Index-level Refs bound to non-render browser APIs
  (`window.history`, `document.title`). NavRef, TitleRef.
- output:     server-owned Refs that render into the body as sinks
  (server pushes via write/append; browser never reads back).
  HeadingRef, TextRef, MarkdownRef, CodeBlockRef, ImageRef, LinkRef,
  BadgeRef, AlertRef, DividerRef, StatRef, ProgressRef, GaugeRef,
  JsonViewerRef, TableRef.
- input:      tab-owned Refs; host reads on demand + subscribes to
  `notify`. ButtonRef, InputRef, NumberInputRef, TextAreaRef,
  CheckboxRef, SwitchRef, SliderRef, SelectRef, RadioGroupRef,
  TagInputRef, DatePickerRef.
- chart:      output sinks with chart-specific payload contracts.
  LineChart, BarChart, AreaChart, PieChart, Sparkline.
- layout:     Shape-based container Sections that mount other Refs.
  Row, Column, Container, Card, Modal, Accordion, Tabs, Fieldset,
  Form, Field.

All names are re-exported flat here so the wire-type resolver
(`_wire_type`) finds them via MRO.
"""

from __future__ import annotations

from nu.ui.core import Ref, Section, SectionRef

from .chart import AreaChart, BarChart, LineChart, PieChart, Sparkline
from .input import (
    ButtonRef,
    CheckboxRef,
    DatePickerRef,
    InputRef,
    NumberInputRef,
    RadioGroupRef,
    SelectRef,
    SliderRef,
    SwitchRef,
    TagInputRef,
    TextAreaRef,
)
from .layout import (
    AccordionRef,
    CardRef,
    Column,
    Container,
    FieldRef,
    Fieldset,
    Form,
    Modal,
    Row,
    TabsRef,
)
from .output import (
    AlertRef,
    BadgeRef,
    CodeBlockRef,
    DividerRef,
    GaugeRef,
    HeadingRef,
    ImageRef,
    JsonViewerRef,
    LinkRef,
    MarkdownRef,
    ProgressRef,
    StatRef,
    TableRef,
    TextRef,
)
from .structural import NavRef, TitleRef


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
    "NumberInputRef",
    "PieChart",
    "ProgressRef",
    "RadioGroupRef",
    "Ref",
    "Row",
    "Section",
    "SectionRef",
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
