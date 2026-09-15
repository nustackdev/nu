"""nudle -- dashboard host that renders the nustd.ui fabric.

Python host: FastAPI serve + ``NudleServer`` fabric + ``server()`` preset,
concrete ``NudleSession`` over ws, Index / Page / PageRef. Wire protocol +
interactions live in ``nustd.ui.core`` (transport-agnostic) and are
re-exported here for convenience. The Vite SPA + PyPI wheel that ships
the compiled bundle live under ``nu/ui/web/nudle/``.
"""

from nustd.ui.core import Append, Changed, Frame, Write, decode, encode

from .fabric import NudleServer, server
from .page import Index, Page, PageRef
from .session import NudleSession, Subscription


__all__ = [
    "Append",
    "Changed",
    "Frame",
    "Index",
    "NudleServer",
    "NudleSession",
    "Page",
    "PageRef",
    "Subscription",
    "Write",
    "decode",
    "encode",
    "server",
]
