"""nudle -- the browser host: Index / Page, the boot term, the serve preset.

``Index`` / ``Page`` / ``PageRef`` and the ``Boot`` term live in ``page``;
``assembly`` stacks the ws server, the session driver and the per-tab fold
into one tree as ``serve``. The wire protocol and the shared ws session live
in ``nustd.ui.core``, the server side in ``nustd.ui.server``, and the Vite SPA
+ PyPI wheel that ships the compiled bundle under ``nu/ui/web/nudle/``.
"""

from __future__ import annotations

from nustd.ui.core import Append, Changed, Frame, Subscription, Write, decode, encode

from .assembly import serve
from .page import Boot, Index, Page, PageRef


__all__ = [
    "Append",
    "Boot",
    "Changed",
    "Frame",
    "Index",
    "Page",
    "PageRef",
    "Subscription",
    "Write",
    "decode",
    "encode",
    "serve",
]
