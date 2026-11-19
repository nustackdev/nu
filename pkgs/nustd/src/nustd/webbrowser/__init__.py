"""Nu webbrowser fabric: a tab opened on a url, once a server answers.

Named after Python's ``webbrowser``, whose ``open`` it calls. Opening a tab
is a write to the browser, so it goes through a Ref like any write:
``BROWSER``, in slot 0 of ``OpenTab``. Waiting for the server is flow, a
look every tenth of a second under a timeout (``tab_opened``).

Surface:
    - Browser: the fabric, what opens a url. The system browser unless a
      tree binds its own (``nu.Provide(MyBrowser, {})``), so a test never
      launches one.
    - BrowserRef, BROWSER: the Ref. Its read yields the bound browser, or
      NULL when none is bound; ``BROWSER.open(url)`` builds the write.
    - OpenTab(ref, url): open a url now, through the bound browser, the
      system one when none is.
    - Listening(host, port), listening: whether a server takes connections
      there, as a query and as plain async Python.
    - tab_opened(url, host, port): open a url once a server takes
      connections, or give up quietly.

Example::

    import nustd.webbrowser as webbrowser

    nu.arun(webbrowser.tab_opened("http://127.0.0.1:8080", "127.0.0.1", 8080))
"""

from __future__ import annotations

from .fabric import Browser
from .interactions import Listening, OpenTab, listening
from .presets import tab_opened
from .refs import BROWSER, BrowserRef


__all__ = [
    "BROWSER",
    "Browser",
    "BrowserRef",
    "Listening",
    "OpenTab",
    "listening",
    "tab_opened",
]
