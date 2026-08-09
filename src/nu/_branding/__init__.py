"""Nu brand kit: palette + logo + shared header. Consumed by _cli and nudle."""

from __future__ import annotations

from .header import DOCS_URL, GITHUB_URL, TAGLINE, render_header
from .logo import logo
from .palette import BLUE, PURPLE


__all__ = [
    "BLUE",
    "DOCS_URL",
    "GITHUB_URL",
    "PURPLE",
    "TAGLINE",
    "logo",
    "render_header",
]
