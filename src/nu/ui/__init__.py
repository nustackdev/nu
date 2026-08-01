"""nu.ui -- component fabric.

Layout under ``src/nu/ui/``:

- ``core/``   -- host-independent UI fabric: ``Ref``, ``Section`` /
                 ``SectionRef``, abstract ``Session`` / ``Subscription``,
                 wire ``Frame`` + interactions (``Write`` / ``Append`` /
                 ``Changed``). Reusable by any host.
- ``refs/``   -- widget kit (Row, Card, Table, Input, ...); depends only on core.
- ``nudle/``  -- Page-based host: ``Page`` / ``Index`` / ``Pages`` +
                 ``NudleSession`` over ws + FastAPI serve fabric.
- ``web/``    -- everything for the browser: npm workspace with ``core``,
                 ``kit``, and the ``nudle`` Vite SPA (also the pypi wheel
                 that ships the compiled SPA).

Public entry stays at ``nu.ui``: this ``__init__`` re-exports the core
fabric, widget kit, and nudle host names so existing ``import nu.ui as
nu_ui`` code keeps working.
"""

from . import core, nudle, refs
from .core import Frame, Ref, Section, SectionRef, Session, Subscription
from .core.interactions import Append, Changed, Write
from .nudle.fabric import NudleServer
from .nudle.page import Index, Page, Pages
from .nudle.session import NudleSession
from .refs import (
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
    NumberInputRef,
    PieChart,
    ProgressRef,
    RadioGroupRef,
    Row,
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
    # Widget kit
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
    "NudleServer",
    "NudleSession",
    "NumberInputRef",
    "Page",
    "Pages",
    "PieChart",
    "ProgressRef",
    "RadioGroupRef",
    "Ref",
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
    "TabsRef",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
    "Write",
    # Submodules
    "core",
    "nudle",
    "refs",
]
