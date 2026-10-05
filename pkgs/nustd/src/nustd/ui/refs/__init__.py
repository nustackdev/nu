"""nudle Refs and Sections.

Grouped by kind, one module per group.

- structural: Index-level Refs bound to non-render browser APIs
  (`window.history`, `document.title`). NavRef, TitleRef.
- output:     server-owned Refs that render into the body as sinks
  (server pushes via write/append; browser never reads back).
  HeadingRef, TextRef, ImageRef, LinkRef, ListRef, BadgeRef, StatusDotRef, KbdRef, ShortcutRef, AlertRef, DividerRef,
  EmptyStateRef, StatRef, ProgressRef, GaugeRef, JsonViewerRef, TableRef.
- input:      tab-owned Refs; host reads on demand + subscribes to
  `notify`. ButtonRef, InputRef, NumberInputRef, TextAreaRef,
  CheckboxRef, SwitchRef, SliderRef, SelectRef, RadioGroupRef,
  TagInputRef, DatePickerRef. Also MarkdownRef and CodeRef, which have
  both faces: read-only by default, editable on request.
- chart:      output sinks with chart-specific payload contracts.
  LineChart, BarChart, AreaChart, PieChart, Sparkline.
- tree:       TreeRef, nested rows that fold; server-owned nodes, one notify
  stream with the intent named in `event` (select, open, toggle, rename,
  move), and an `on_*` per intent.
- layout:     Shape-based container Sections that mount other Refs.
  Row, Column, Container, Card, Modal, Accordion, Tabs, Fieldset,
  Form, Field.

All names are re-exported flat here, so `nustd.ui.refs.TextRef` works
whichever module a widget actually lives in.

Two conventions hold across the kit.

`_wire_type`: every class here declares the browser component it renders
as. It is an ordinary inherited ClassVar, so `class Toolbar(Row)` reports
`Row` without anyone walking anything, and an out-of-tree Ref that ships
its own component just declares its own.

`set()`: a Ref with a single semantically primary value exposes `set()`
for it -- `TextRef.set(text)`, `SliderRef.set(n)`, `StatRef.set(value)` --
with the rest of what it can drive on `set_*` kwargs or `set_*` methods.
Having a primary value is the whole test, and most layout Sections fail
it: Row, Column, Card, Fieldset and Tabs wrap their children and carry
nothing of their own, so they get no `set()`. Modal has one anyway, and
is not an exception to the rule so much as the rule biting: open vs
closed is the thing a modal carries.
"""

from __future__ import annotations

from nustd.ui.core import Ref, Section, SectionRef

from .chart import AreaChart, BarChart, LineChart, PieChart, Sparkline
from .input import (
    ButtonRef,
    CheckboxRef,
    CodeRef,
    DatePickerRef,
    InputRef,
    MarkdownRef,
    NumberInputRef,
    RadioGroupRef,
    SelectRef,
    SliderRef,
    SwitchRef,
    TagInputRef,
    TextAreaRef,
)
from .layout import (
    Accordion,
    AccordionRef,
    Card,
    CardRef,
    Column,
    Container,
    Field,
    FieldRef,
    Fieldset,
    FieldsetRef,
    Form,
    Modal,
    ModalRef,
    Row,
    Tabs,
    TabsRef,
)
from .output import (
    AlertRef,
    BadgeRef,
    DividerRef,
    EmptyStateRef,
    GaugeRef,
    HeadingRef,
    ImageRef,
    JsonViewerRef,
    KbdRef,
    LinkRef,
    ListRef,
    ProgressRef,
    ShortcutRef,
    StatRef,
    StatusDotRef,
    TableRef,
    TextRef,
)
from .structural import NavRef, TitleRef
from .tree import TreeRef


__all__ = [
    "Accordion",
    "AccordionRef",
    "AlertRef",
    "AreaChart",
    "BadgeRef",
    "BarChart",
    "ButtonRef",
    "Card",
    "CardRef",
    "CheckboxRef",
    "CodeRef",
    "Column",
    "Container",
    "DatePickerRef",
    "DividerRef",
    "EmptyStateRef",
    "Field",
    "FieldRef",
    "Fieldset",
    "FieldsetRef",
    "Form",
    "GaugeRef",
    "HeadingRef",
    "ImageRef",
    "InputRef",
    "JsonViewerRef",
    "KbdRef",
    "LineChart",
    "LinkRef",
    "ListRef",
    "MarkdownRef",
    "Modal",
    "ModalRef",
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
    "ShortcutRef",
    "SliderRef",
    "Sparkline",
    "StatRef",
    "StatusDotRef",
    "SwitchRef",
    "TableRef",
    "Tabs",
    "TabsRef",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
    "TreeRef",
]
