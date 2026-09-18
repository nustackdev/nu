"""Shared Nu header: logo on the left, tagline + version + urls on the right.

Used by the CLI (`nu` with no args) and the nudle server banner -- one
shared visual identity across every user-facing entrypoint.

The two columns are laid out by hand (a fixed-width left cell, four spaces
of gutter, a right cell padded to its widest line, right block vertically
centred against the mark) so the kernel needs no table renderer.
"""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

from .ansi import color_enabled, paint
from .logo import WIDTH as _LOGO_WIDTH
from .logo import logo_lines
from .palette import BLUE


if TYPE_CHECKING:
    from typing import IO


TAGLINE = "The interaction primitive"
DOCS_URL = "https://nustack.dev"
GITHUB_URL = "https://github.com/nustackdev/nu"

# Gutter between the mark and the label block.
_GUTTER = "    "


def _nu_version() -> str:
    try:
        return version("nucore")
    except PackageNotFoundError:
        return "0.0.0+dev"


def _side(color: bool) -> list[tuple[str, str]]:
    """The right-hand label block as ``(plain, rendered)`` lines."""
    ver = f"v{_nu_version()}"
    return [
        (TAGLINE, TAGLINE),
        (ver, paint(ver, fg=BLUE, bold=True, enabled=color)),
        ("", ""),
        (DOCS_URL, paint(DOCS_URL, fg=BLUE, underline=True, enabled=color)),
        ("", ""),
        (GITHUB_URL, paint(GITHUB_URL, fg=BLUE, underline=True, enabled=color)),
    ]


def header(*, color: bool = True) -> str:
    """The header block as one string, blank line above and below."""
    # ``logo`` ends on a newline, so the mark occupies one blank row past its
    # last glyph row -- that row is part of the block and gets padded too.
    # Every glyph row is exactly ``_LOGO_WIDTH`` cells wide, so the left column
    # needs no padding of its own; the trailing row is that width in spaces.
    left = [*logo_lines(color=color), " " * _LOGO_WIDTH]

    side = _side(color)
    right_width = max(len(plain) for plain, _ in side)
    # Vertically centre the labels against the mark, rich's ``vertical="middle"``.
    top = (len(left) - len(side)) // 2
    blank = ("", "")
    rows = [blank] * top + side + [blank] * (len(left) - len(side) - top)

    lines = [""]
    for mark, (plain, rendered) in zip(left, rows, strict=True):
        lines.append(mark + _GUTTER + rendered + " " * (right_width - len(plain)))
    lines.append("")
    return "\n".join(lines)


def render_header(file: IO[str] | None = None) -> None:
    """Print the shared Nu header: logo on the left, labels on the right."""
    stream = sys.stdout if file is None else file
    print(header(color=color_enabled(stream)), file=stream, flush=True)
