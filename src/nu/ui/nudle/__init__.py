"""nudle -- dashboard app that hosts the nu.ui fabric.

Python host (this package): serve, session, Page/Pages/Index, presets,
protocol, interactions. The Vite SPA + PyPI wheel that ships the compiled
bundle live under ``nu/ui/web/nudle/``.
"""

from . import interactions, presets, protocol, session
from .fabric import NudleServer
from .interactions import Append, Changed, Write
from .page import Index, Page, Pages
from .protocol import Frame, decode, encode
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
    "interactions",
    "presets",
    "protocol",
    "session",
]
