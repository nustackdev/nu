"""nudle -- the browser host: the serve preset, and nudle's telemetry.

nudle decides nothing about what is on screen. The program draws the whole
tree (``nustd.ui.boot`` brings up what is always there, ``nustd.ui.route``
runs the branch the pathname names) and the browser renders it, links
included, inside the kit's AnchorCatcher.

``driver`` stacks the ws server, the session driver and the per-tab fold
into one tree as ``serve``; ``telemetry`` is nudle's own opt-out usage ping.
The wire protocol and the shared ws session live in ``nustd.ui.core``, the
connection lifecycle in ``nustd.ws_server``, and the Vite SPA + PyPI wheel
that ships the compiled bundle from ``pkgs/ts/nudle``.
"""

from __future__ import annotations

from nustd.ui.core import Append, Changed, Frame, Send, Subscription, Write, decode, encode

from .driver import serve


__all__ = [
    "Append",
    "Changed",
    "Frame",
    "Send",
    "Subscription",
    "Write",
    "decode",
    "encode",
    "serve",
]
