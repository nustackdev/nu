"""nustd.ui Refs: layer 1, the widget kit as Refs.

Refs express any UI alone. A container Ref built with ``parent_ref=`` and
``props=`` is a whole container, and the address is a term, so computed keys
under one parent repeat a child as many times as there are keys::

    card = CardRef("card", parent_ref=page, props={"title": "Hosts"})
    row = RowRef(nu.Str("r") + nu.str(i), parent_ref=card)
    TextRef("name", parent_ref=row).set(name)

The Shapes in ``nustd.ui.shapes`` are layer 2, a declarative DSL over the
container Refs, and draw nothing a Ref could not.

Layout under ``refs/``:

- containers/: open-ended children, optional chrome. ``ContainerRef``
  (base); flow (``ColumnRef``, ``RowRef``, ``GridRef``, ``LineRef``);
  chrome (``CardRef``, ``BoxRef`` behind the Box, ``TabsRef``,
  ``ModalRef``, ``AccordionRef``, ``FormRef``, ``FieldsetRef``,
  ``FieldRef``); disclosure (``CollapsibleRef``, ``SheetRef``); and
  ``ListRef``, whose items are its plain strings and then any child node.
- leaves/: one thing drawn from props, never children. ``LeafRef`` (base);
  output (``HeadingRef``, ``TextRef``, ``ImageRef``, ``LinkRef``,
  ``BadgeRef``, ``StatusDotRef``, ``KbdRef``, ``ShortcutRef``, ``AlertRef``,
  ``DividerRef``, ``EmptyStateRef``, ``StatRef``, ``ProgressRef``,
  ``GaugeRef``, ``JsonViewerRef``); display (``AvatarRef``,
  ``BreadcrumbRef``, ``SkeletonRef``, ``SpinnerRef``, ``StatusPillRef``);
  table (``TableRef`` and its row ops); tree (``TreeRef``); input (tab-owned:
  ``ButtonRef``, ``InputRef``, ``ToggleRef``, ..., plus ``MarkdownRef`` and
  ``CodeRef``, read-only by default and editable on request); and chart
  (``Chart``, one ECharts option, and typed builders over it: ``LineChart``,
  ``BarChart``, ``PieChart``, ``HeatmapChart``, ``Sparkline``, ...).
- structural.py: Index-level leaves bound to non-render browser APIs
  (``window.history``, ``document.title``). ``NavRef``, ``TitleRef``.
- layout.py, output.py, input.py, chart.py, tree.py: kept for old import
  paths, re-exports only.

Something is a container only when its children are open-ended user
composition. Fixed known parts are props on a leaf: a button's label and
icon are props, not children. Building a Ref with ``parent_ref=`` a leaf
raises ``TypeError``.

All names are re-exported flat here, so ``nustd.ui.refs.TextRef`` works
whichever module a widget actually lives in. The Shapes are re-exported too
(``nustd.ui.refs.Row`` has always worked). That is the one layering
exception, and it is why this module imports ``containers`` and ``leaves``
before ``nustd.ui.shapes``: the Shapes build on the container Refs, and
nothing under ``refs/`` imports a Shape.

Two conventions hold across the kit.

`_wire_type`: every Ref here declares the browser component it renders as.
It is an ordinary inherited ClassVar, so ``class Label(TextRef)`` reports
``TextRef`` without anyone walking anything, and an out-of-tree Ref that
ships its own component just declares its own. Shapes declare none: they
take their Ref's, so ``class Toolbar(Row)`` reports ``Row`` by way of
``RowRef``. The two abstract bases declare an empty one and never reach the
wire.

`set()`: a Ref with a single semantically primary value exposes `set()`
for it -- `TextRef.set(text)`, `SliderRef.set(n)`, `StatRef.set(value)` --
with the rest of what it can drive on `set_*` kwargs or `set_*` methods.
Having a primary value is the whole test, and most containers fail it:
Row, Column, Card, Fieldset and Tabs wrap their children and carry nothing
of their own, so they get no `set()`. Modal has one anyway, and is not an
exception to the rule so much as the rule biting: open vs closed is the
thing a modal carries. ``ListRef`` keeps its old ``set(items)`` for plain
string items.
"""

from __future__ import annotations

from nustd.ui.core import Ref, Section, SectionRef

from .containers import (
    AccordionRef,
    BoxRef,
    CardRef,
    CollapsibleRef,
    ColumnRef,
    ContainerRef,
    DictContainerRef,
    FieldRef,
    FieldsetRef,
    FormRef,
    GridRef,
    LineRef,
    ListContainerRef,
    ListRef,
    ModalRef,
    RowRef,
    ShapeContainerRef,
    SheetRef,
    TabsRef,
)
from .leaves import (
    AlertRef,
    AreaChart,
    AvatarRef,
    BadgeRef,
    BarChart,
    BoxplotChart,
    BreadcrumbRef,
    ButtonRef,
    CandlestickChart,
    Chart,
    CheckboxRef,
    CodeRef,
    DatePickerRef,
    DividerRef,
    EmptyStateRef,
    FunnelChart,
    GaugeChart,
    GaugeRef,
    HeadingRef,
    HeatmapChart,
    Histogram,
    ImageRef,
    InputRef,
    InsertRow,
    JsonViewerRef,
    KbdRef,
    LeafRef,
    LineChart,
    LinkRef,
    MarkdownRef,
    NumberInputRef,
    PieChart,
    ProgressRef,
    RadarChart,
    RadioGroupRef,
    RemoveRows,
    SankeyChart,
    ScatterChart,
    SelectRef,
    SetOrder,
    SetRow,
    ShortcutRef,
    SkeletonRef,
    SketchRef,
    SliderRef,
    Sparkline,
    SpinnerRef,
    StatRef,
    StatusDotRef,
    StatusPillRef,
    SunburstChart,
    SwitchRef,
    TableRef,
    TagInputRef,
    TextAreaRef,
    TextRef,
    ToggleRef,
    TreemapChart,
    TreeRef,
)
from .structural import NavRef, TitleRef


# isort: split
# Layer 2 last, after every Ref it builds on (see the module docstring).
from nustd.ui.shapes import (
    Accordion,
    Box,
    Card,
    Collapsible,
    Column,
    Field,
    Fieldset,
    Form,
    Grid,
    Line,
    List,
    Modal,
    Row,
    Sheet,
    Tabs,
)


__all__ = [
    "Accordion",
    "AccordionRef",
    "AlertRef",
    "AreaChart",
    "AvatarRef",
    "BadgeRef",
    "BarChart",
    "Box",
    "BoxRef",
    "BoxplotChart",
    "BreadcrumbRef",
    "ButtonRef",
    "CandlestickChart",
    "Card",
    "CardRef",
    "Chart",
    "CheckboxRef",
    "CodeRef",
    "Collapsible",
    "CollapsibleRef",
    "Column",
    "ColumnRef",
    "ContainerRef",
    "DatePickerRef",
    "DictContainerRef",
    "DividerRef",
    "EmptyStateRef",
    "Field",
    "FieldRef",
    "Fieldset",
    "FieldsetRef",
    "Form",
    "FormRef",
    "FunnelChart",
    "GaugeChart",
    "GaugeRef",
    "Grid",
    "GridRef",
    "HeadingRef",
    "HeatmapChart",
    "Histogram",
    "ImageRef",
    "InputRef",
    "InsertRow",
    "JsonViewerRef",
    "KbdRef",
    "LeafRef",
    "Line",
    "LineChart",
    "LineRef",
    "LinkRef",
    "List",
    "ListContainerRef",
    "ListRef",
    "MarkdownRef",
    "Modal",
    "ModalRef",
    "NavRef",
    "NumberInputRef",
    "PieChart",
    "ProgressRef",
    "RadarChart",
    "RadioGroupRef",
    "Ref",
    "RemoveRows",
    "Row",
    "RowRef",
    "SankeyChart",
    "ScatterChart",
    "Section",
    "SectionRef",
    "SelectRef",
    "SetOrder",
    "SetRow",
    "ShapeContainerRef",
    "Sheet",
    "SheetRef",
    "ShortcutRef",
    "SkeletonRef",
    "SketchRef",
    "SliderRef",
    "Sparkline",
    "SpinnerRef",
    "StatRef",
    "StatusDotRef",
    "StatusPillRef",
    "SunburstChart",
    "SwitchRef",
    "TableRef",
    "Tabs",
    "TabsRef",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
    "ToggleRef",
    "TreeRef",
    "TreemapChart",
]
