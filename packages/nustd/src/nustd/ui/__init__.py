"""nustd.ui -- component fabric.

Layout under ``src/nu/ui/``:

- ``core/``   -- host-independent UI fabric: ``Ref``, ``Section`` /
                 ``SectionRef``, abstract ``Session`` / ``Subscription``,
                 wire ``Frame`` + interactions (``Write`` / ``Append`` /
                 ``Remove`` / ``Changed``). Reusable by any host.
- ``refs/``   -- widget kit (Row, Card, Table, Input, ...); depends only on core.
- ``nudle/``  -- Page-based host: ``Index`` / ``Page`` / ``PageRef``, the
                 ``Boot`` term, and the ``serve`` preset that assembles a
                 whole tree.
- ``server/`` -- the ws host: uvicorn lifecycle, a registry holding one row
                 per live connection, and the Nu driver that relays
                 connections into the tree.
- ``web/``    -- everything for the browser: npm workspace with ``core``,
                 ``kit``, and the ``nudle`` Vite SPA (also the pypi wheel
                 that ships the compiled SPA).

Public entry stays at ``nustd.ui``: this ``__init__`` re-exports the core
fabric, widget kit, and nudle host names so existing ``import nustd.ui as
nu_ui`` code keeps working.
"""

from . import core, nudle, refs, server
from .core import Frame, Ref, Section, SectionRef, Session, Subscription, WsSession
from .core.interactions import Append, Changed, Remove, Write
from .nudle import serve
from .nudle.page import Boot, Index, Page, PageRef
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
from .server import web_server


__all__ = [
    # Widget kit
    "Accordion",
    "AlertRef",
    "Append",
    "AreaChart",
    "BadgeRef",
    "BarChart",
    "Boot",
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
    "WsSession",
    # Submodules and presets, in one ASCII sort -- which is why `serve` the
    # preset sits next to `server` the package it assembles.
    "core",
    "nudle",
    "refs",
    "serve",
    "server",
    "web_server",
]
