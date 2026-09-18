"""Nu brand kit: palette + logo + shared header. Consumed by nudle and nucli.

Stdlib only -- it renders straight to ANSI escapes (see :mod:`.ansi`), so it
sits in the kernel without pulling a terminal library in behind it.
"""

from __future__ import annotations

from .ansi import RESET, color_enabled, paint
from .header import DOCS_URL, GITHUB_URL, TAGLINE, header, render_header
from .logo import logo, logo_lines
from .palette import BLUE, PURPLE


__all__ = [
    "BLUE",
    "DOCS_URL",
    "GITHUB_URL",
    "PURPLE",
    "RESET",
    "TAGLINE",
    "color_enabled",
    "header",
    "logo",
    "logo_lines",
    "paint",
    "render_header",
]
