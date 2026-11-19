"""Browser: the fabric a tab is opened through, the system browser by default."""

from __future__ import annotations

import webbrowser

import nu


__all__ = ["SYSTEM", "Browser", "browser_of"]


class Browser(nu.Fabric):
    """What opens a url: the system browser. Bind a subclass to redirect it.

    Notes:
        - Nothing to set up or clean up: opening a tab is a hand over to
          the system, sync and quick.
        - A subclass binds as ``Browser``, so ``BROWSER`` finds it.
    """

    def open(self, url: str) -> None:
        """Open ``url`` in a tab."""
        webbrowser.open(url)


# Every subclass binds under the base, the class ``BrowserRef`` looks up.
Browser._nu_bind_as = Browser  # pyright: ignore[reportAttributeAccessIssue]

#: The system browser, used when no ``Browser`` is bound.
SYSTEM = Browser()


def browser_of(value: object) -> Browser:
    """The browser a ``BrowserRef`` read: the bound one, else the system browser."""
    return value if isinstance(value, Browser) else SYSTEM
