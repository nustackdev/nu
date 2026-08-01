"""nu.ui -- component fabric.

Layout under ``src/nu/ui/``:

- ``py/`` -- python side of the fabric (widget kit under ``py/refs``)
- ``ts/`` -- typescript side (npm packages: ``core``, ``kit``)
- ``nudle/`` -- the nudle dashboard app that hosts the fabric (its own
  ``py/`` host + ``ts/`` SPA)

Public entry stays at ``nu.ui``: this ``__init__`` re-exports the widget
kit + host names so existing ``import nu.ui as nu_ui`` code keeps working.
"""

from .nudle.py import interactions, presets, protocol, session
from .nudle.py.fabric import NudleServer
from .nudle.py.interactions import Append, Changed, Write
from .nudle.py.page import Index, Page, Pages
from .nudle.py.protocol import Frame, decode, encode
from .nudle.py.session import NudleSession, Subscription
from .py import refs
from .py.refs import (
    AccordionRef,
    AlertRef,
    AreaChart,
    BadgeRef,
    BarChart,
    ButtonRef,
    CardRef,
    CheckboxRef,
    CodeBlockRef,
    Column,
    Container,
    DatePickerRef,
    DividerRef,
    FieldRef,
    Fieldset,
    Form,
    GaugeRef,
    HeadingRef,
    ImageRef,
    InputRef,
    JsonViewerRef,
    LineChart,
    LinkRef,
    MarkdownRef,
    Modal,
    NavRef,
    NudleRef,
    NumberInputRef,
    PieChart,
    ProgressRef,
    RadioGroupRef,
    Row,
    Section,
    SelectRef,
    SliderRef,
    Sparkline,
    StatRef,
    SwitchRef,
    TableRef,
    TabsRef,
    TagInputRef,
    TextAreaRef,
    TextRef,
    TitleRef,
)


__all__ = [
    # Names
    "AccordionRef",
    "AlertRef",
    "Append",
    "AreaChart",
    "BadgeRef",
    "BarChart",
    "ButtonRef",
    "CardRef",
    "Changed",
    "CheckboxRef",
    "CodeBlockRef",
    "Column",
    "Container",
    "DatePickerRef",
    "DividerRef",
    "FieldRef",
    "Fieldset",
    "Form",
    "Frame",
    "GaugeRef",
    "HeadingRef",
    "ImageRef",
    "Index",
    "InputRef",
    "JsonViewerRef",
    "LineChart",
    "LinkRef",
    "MarkdownRef",
    "Modal",
    "NavRef",
    "NudleRef",
    "NudleServer",
    "NudleSession",
    "NumberInputRef",
    "Page",
    "Pages",
    "PieChart",
    "ProgressRef",
    "RadioGroupRef",
    "Row",
    "Section",
    "SelectRef",
    "SliderRef",
    "Sparkline",
    "StatRef",
    "Subscription",
    "SwitchRef",
    "TableRef",
    "TabsRef",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
    "Write",
    # Submodules
    "decode",
    "encode",
    "interactions",
    "page",
    "presets",
    "protocol",
    "refs",
    "session",
]
