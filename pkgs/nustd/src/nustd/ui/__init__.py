"""nustd.ui -- component fabric.

Layout under ``src/nustd/ui/``:

- ``core/``   -- host-independent UI fabric: ``Ref``, ``Section`` /
                 ``SectionRef``, abstract ``Session`` / ``Subscription``,
                 wire ``Frame`` + interactions (``Write`` / ``Append`` /
                 ``Remove`` / ``Changed``). Reusable by any host.
- ``refs/``   -- widget kit (Row, Card, Table, Input, ...); depends only on core.
- ``nudle/``  -- Page-based host: ``Index`` / ``Page`` / ``PageRef``, the
                 ``Boot`` term, and the ``serve`` preset that assembles a
                 whole tree.

The uvicorn lifecycle, the book of live connections and the per-connection
fold live in ``nustd.ws_server``, which knows nothing about ui.

The browser half is not in this package. It lives in the repo's npm workspace
at ``pkgs/ts`` (``ui-core``, ``ui-kit``, and the ``nudle`` Vite app), and its
compiled bundle ships as the separate ``nudle`` wheel.

The public entry is ``nustd.ui`` itself: the core fabric, the widget kit and
the nudle host names are re-exported flat, so one ``import nustd.ui`` reaches
everything a UI program spells.
"""

from . import core, nudle, refs
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
    MonacoRef,
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
    "MonacoRef",
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
    # Submodules and presets
    "core",
    "nudle",
    "refs",
    "serve",
]
