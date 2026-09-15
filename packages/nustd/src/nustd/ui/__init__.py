"""nustd.ui -- component fabric.

Layout under ``src/nu/ui/``:

- ``core/``   -- host-independent UI fabric: ``Ref``, ``Section`` /
                 ``SectionRef``, abstract ``Session`` / ``Subscription``,
                 wire ``Frame`` + interactions (``Write`` / ``Append`` /
                 ``Remove`` / ``Changed``). Reusable by any host.
- ``refs/``   -- widget kit (Row, Card, Table, Input, ...); depends only on core.
- ``nudle/``  -- Page-based host: ``Index`` / ``Page`` / ``PageRef`` +
                 ``NudleSession`` over ws + FastAPI serve fabric.
- ``web/``    -- everything for the browser: npm workspace with ``core``,
                 ``kit``, and the ``nudle`` Vite SPA (also the pypi wheel
                 that ships the compiled SPA).

Public entry stays at ``nustd.ui``: this ``__init__`` re-exports the core
fabric, widget kit, and nudle host names so existing ``import nustd.ui as
nu_ui`` code keeps working.
"""

from . import core, nudle, refs
from .core import Frame, Ref, Section, SectionRef, Session, Subscription
from .core.interactions import Append, Changed, Remove, Write
from .nudle.fabric import NudleServer, server
from .nudle.page import Index, Page, PageRef
from .nudle.session import NudleSession
from .refs import (
    Accordion,
    AlertRef,
    AreaChart,
    BadgeRef,
    BarChart,
    ButtonRef,
    Card,
    CheckboxRef,
    CodeBlockRef,
    Column,
    Container,
    DatePickerRef,
    DividerRef,
    Field,
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
    NumberInputRef,
    PieChart,
    ProgressRef,
    ProseRef,
    RadioGroupRef,
    Row,
    SelectRef,
    SliderRef,
    Sparkline,
    StatRef,
    SwitchRef,
    TableRef,
    Tabs,
    TagInputRef,
    TextAreaRef,
    TextRef,
    TitleRef,
)


__all__ = [
    # Widget kit
    "Accordion",
    "AlertRef",
    "Append",
    "AreaChart",
    "BadgeRef",
    "BarChart",
    "ButtonRef",
    "Card",
    "Changed",
    "CheckboxRef",
    "CodeBlockRef",
    "Column",
    "Container",
    "DatePickerRef",
    "DividerRef",
    "Field",
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
    "NudleServer",
    "NudleSession",
    "NumberInputRef",
    "Page",
    "PageRef",
    "PieChart",
    "ProgressRef",
    "ProseRef",
    "RadioGroupRef",
    "Ref",
    "Remove",
    "Row",
    "Section",
    "SectionRef",
    "SelectRef",
    "Session",
    "SliderRef",
    "Sparkline",
    "StatRef",
    "Subscription",
    "SwitchRef",
    "TableRef",
    "Tabs",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
    "Write",
    # Submodules
    "core",
    "nudle",
    "refs",
    # Presets
    "server",
]
