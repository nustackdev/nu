"""nu.ui -- component fabric.

Layout under ``src/nu/ui/``:

- ``refs/``   -- python widget kit
- ``nudle/``  -- python nudle host (serve, session, Page, presets, ...)
- ``web/``    -- everything for the browser: npm workspace with ``core``,
                 ``kit``, and the ``nudle`` Vite SPA (also the pypi wheel
                 that ships the compiled SPA).

Public entry stays at ``nu.ui``: this ``__init__`` re-exports the widget
kit + host names so existing ``import nu.ui as nu_ui`` code keeps working.
"""

from . import refs
from .nudle import interactions, presets, protocol, session
from .nudle.fabric import NudleServer
from .nudle.interactions import Append, Changed, Write
from .nudle.page import Index, Page, Pages
from .nudle.protocol import Frame, decode, encode
from .nudle.session import NudleSession, Subscription
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
