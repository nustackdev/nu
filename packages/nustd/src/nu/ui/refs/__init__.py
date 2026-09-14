"""nudle Refs and Sections.

Grouped by kind, one module per group.

- structural: Index-level Refs bound to non-render browser APIs
  (`window.history`, `document.title`). NavRef, TitleRef.
- output:     server-owned Refs that render into the body as sinks
  (server pushes via write/append; browser never reads back).
  HeadingRef, TextRef, MarkdownRef, CodeBlockRef, ImageRef, LinkRef,
  BadgeRef, AlertRef, DividerRef, StatRef, ProgressRef, GaugeRef,
  JsonViewerRef, TableRef.
- input:      tab-owned Refs; host reads on demand + subscribes to
  `notify`. ButtonRef, InputRef, NumberInputRef, TextAreaRef,
  ProseRef, CheckboxRef, SwitchRef, SliderRef, SelectRef,
  RadioGroupRef, TagInputRef, DatePickerRef.
- chart:      output sinks with chart-specific payload contracts.
  LineChart, BarChart, AreaChart, PieChart, Sparkline.
- layout:     Shape-based container Sections that mount other Refs.
  Row, Column, Container, Card, Modal, Accordion, Tabs, Fieldset,
  Form, Field.

All names are re-exported flat here, so `nu.ui.refs.TextRef` works
whichever module a widget actually lives in.

Two conventions hold across the kit.

`_wire_type`: every class here declares the browser component it renders
as. It is an ordinary inherited ClassVar, so `class Toolbar(Row)` reports
`Row` without anyone walking anything, and an out-of-tree Ref that ships
its own component just declares its own.

`set()`: a Ref with a single semantically primary value exposes `set()`
for it -- `TextRef.set(text)`, `SliderRef.set(n)`, `StatRef.set(value)` --
with the rest of what it can drive on `set_*` kwargs or `set_*` methods.
A container has no primary value, so it gets no `set()` at all: Row,
Column, Card, Fieldset, Tabs and the other layout Sections wrap their
children, not a value. Modal is the one layout exception, because open
vs closed genuinely is the thing it carries.
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
    ProseRef,
    RadioGroupRef,
    SelectRef,
    SliderRef,
    SwitchRef,
    TagInputRef,
    TextAreaRef,
)
from .layout import (
    Accordion,
    Card,
    Column,
    Container,
    Field,
    Fieldset,
    Form,
    Modal,
    Row,
    Tabs,
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
    "Accordion",
    "AlertRef",
    "AreaChart",
    "BadgeRef",
    "BarChart",
    "ButtonRef",
    "Card",
    "CheckboxRef",
    "CodeBlockRef",
    "Column",
    "Container",
    "DatePickerRef",
    "DividerRef",
    "Field",
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
    "ProseRef",
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
    "Tabs",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
]
