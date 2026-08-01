"""nudle -- dashboard host that renders the nu.ui fabric.

Python host: FastAPI serve + ``NudleServer`` fabric + ``server()`` preset,
concrete ``NudleSession`` over ws, Page / Pages / Index. Wire protocol +
interactions live in ``nu.ui.core`` (transport-agnostic) and are
re-exported here for convenience. The Vite SPA + PyPI wheel that ships
the compiled bundle live under ``nu/ui/web/nudle/``.
"""

from nu.ui.core import Append, Changed, Frame, Write, decode, encode

from .fabric import NudleServer, server
from .page import Index, Page, Pages
from .session import NudleSession, Subscription


__all__ = [
    "Append",
    "Changed",
    "Frame",
    "Index",
    "NudleServer",
    "NudleSession",
    "Page",
    "Pages",
    "Subscription",
    "Write",
    "decode",
    "encode",
    "server",
]
