"""Page Shapes -- PageSection and NavList, declared.

Each is a Section over its container Ref (``nustd.ui.refs.containers.page``):
the Ref carries the chrome methods, the slot defaults and the wire type, and
``slot(**props)`` forwards to it.

    class Usage(PageSection):
        actions = ButtonRef.slot(label="Export", variant="secondary")
        stats = Stats.slot(columns=3)

    class Sidebar(NavList):
        home = NavItemRef.slot(label="Home", href="/", icon="home")
        docs = NavItemRef.slot(label="Docs", href="/docs", icon="book-open")

    usage = Usage.slot(title="Usage", description="Last 30 days")
    sidebar = Sidebar.slot(label="Workspace")

A slot named ``actions`` draws on the section header's right, not the body.
"""

from __future__ import annotations

from nustd.ui.core import Section
from nustd.ui.refs.containers.page import NavListRef, PageSectionRef


__all__ = ["NavList", "PageSection"]


class PageSection(Section):
    """A titled part of a page, its slots the body. Props as ``PageSectionRef.slot``.

    A slot named ``actions`` draws on the header's right instead of the body;
    ``section.actions`` reaches it.
    """

    _ref_cls = PageSectionRef


class NavList(Section):
    """Its slots as a sidebar list or a top bar. Props as ``NavListRef.slot``."""

    _ref_cls = NavListRef
