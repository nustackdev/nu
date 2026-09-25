"""nustd.ui -- component fabric.

Layout under ``src/nustd/ui/``:

- ``lens/``   -- the Shape lens: ``LensRef``, the walk that turns a Shape and
                 a cursor into columns, and ``browse`` to assemble the two.
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
everything a UI program spells. The lens is the exception and stays whole
behind ``nustd.ui.lens``, ``LensRef`` included: it is a subsystem rather than
a widget, and a surface split between two names is worse than one more dot.

**The host half loads on first use.** Building Refs and serving them are two
different jobs and only one of them needs a web server: ``nudle`` reaches
``nustd.ws_server``, which reaches uvicorn and fastapi, and that was most of
what ``import nustd.ui`` cost. Plenty of processes only ever build Refs. The
case that made this worth doing is a worker drawing on a connection it holds
a proxy to: it pays the import on every launch and serves nothing, ever. So
``nudle``, ``serve`` and the four page names come through ``__getattr__``
below, and naming any of them loads the host with its server, which is what
somebody naming them is asking for.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from . import core, lens, refs
from .core import Frame, Ref, Section, SectionRef, Session, Subscription, WsSession
from .core.interactions import Append, Changed, Remove, Write
from .refs import (
    Accordion,
    AccordionRef,
    AlertRef,
    AreaChart,
    BadgeRef,
    BarChart,
    ButtonRef,
    Card,
    CardRef,
    CheckboxRef,
    CodeBlockRef,
    Column,
    Container,
    DatePickerRef,
    DividerRef,
    EmptyStateRef,
    Field,
    FieldRef,
    Fieldset,
    FieldsetRef,
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
    ModalRef,
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
    StatusDotRef,
    SwitchRef,
    TableRef,
    Tabs,
    TabsRef,
    TagInputRef,
    TextAreaRef,
    TextRef,
    TitleRef,
)


# The host half, handed to IDEs and type-checkers as the real thing, so
# ``nustd.ui.Page`` resolves statically with completion and go-to-definition
# despite never being bound at import time.
if TYPE_CHECKING:
    from . import nudle
    from .nudle import serve
    from .nudle.page import Boot, Index, Page, PageRef


#: Every name the host half contributes, and the module each one is in.
#: ``nudle`` maps to itself: the package is one of the names.
_LAZY = {
    "Boot": ".nudle.page",
    "Index": ".nudle.page",
    "Page": ".nudle.page",
    "PageRef": ".nudle.page",
    "nudle": ".nudle",
    "serve": ".nudle",
}


def __getattr__(name: str) -> object:
    """One host name, imported by the first access that asks for it.

    Cached into the module's own globals on the way out, so the import and
    this lookup are both paid once. Anything not the host's is the ordinary
    ``AttributeError``, unchanged.
    """
    where = _LAZY.get(name)
    if where is None:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
    module = importlib.import_module(where, __name__)
    value = module if name == "nudle" else getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Everything reachable here, whether or not it has been loaded yet."""
    return sorted({*globals(), *_LAZY})


__all__ = [
    # Widget kit
    "Accordion",
    "AccordionRef",
    "AlertRef",
    "Append",
    "AreaChart",
    "BadgeRef",
    "BarChart",
    "Boot",
    "ButtonRef",
    "Card",
    "CardRef",
    "Changed",
    "CheckboxRef",
    "CodeBlockRef",
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
    "ModalRef",
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
    "StatusDotRef",
    "Subscription",
    "SwitchRef",
    "TableRef",
    "Tabs",
    "TabsRef",
    "TagInputRef",
    "TextAreaRef",
    "TextRef",
    "TitleRef",
    "Write",
    "WsSession",
    # Submodules and presets
    "core",
    "lens",
    "nudle",
    "refs",
    "serve",
]
