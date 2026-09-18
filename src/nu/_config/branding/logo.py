"""Nu mark rendered as terminal braille glyphs.

Compact 2x4 sub-pixel braille packing of the SVG mark -- two interlocking
glyphs, purple top-left and blue bottom-right matching the SVG gradient
stops.

Baked once from the source PNG so this module has zero runtime deps beyond
the stdlib.
"""

from __future__ import annotations

from .ansi import paint
from .palette import BLUE, PURPLE


_COLOR = {"P": PURPLE, "B": BLUE}

# 16 cols x 8 rows braille grid; each row is (glyphs, per-cell color tag —
# 'P' purple, 'B' blue, '.' blank).
_LOGO: tuple[tuple[str, str], ...] = (
    ("⠀⢀⣤⣶⣾⣿⣿⣿⣿⣿⣿⡇⠀⢰⣿⣿", ".PPPPPPPPPPP.PPB"),
    ("⣰⣿⣿⠟⠋⠉⠉⠉⠉⣿⣿⡇⠀⢸⣿⣿", "PPPPPPPPPPPP.BBB"),
    ("⣿⣿⡇⠀⠀⣀⣀⠀⠀⣿⣿⡇⠀⢸⣿⣿", "PPP..PP..PPB.BBB"),
    ("⣿⣿⡇⠀⢸⣿⣿⠀⠀⣿⣿⡇⠀⢸⣿⣿", "PPP.PPP..BBB.BBB"),
    ("⣿⣿⡇⠀⢸⣿⣿⠀⠀⣿⣿⡇⠀⢸⣿⣿", "PPP.PPP..BBB.BBB"),
    ("⣿⣿⡇⠀⢸⣿⣿⠀⠀⠉⠉⠀⠀⢸⣿⣿", "PPP.PBB..BB..BBB"),
    ("⣿⣿⡇⠀⢸⣿⣿⣀⣀⣀⣀⣠⣴⣿⣿⠏", "PPP.BBBBBBBBBBBB"),
    ("⣿⣿⠇⠀⢸⣿⣿⣿⣿⣿⣿⡿⠿⠛⠁⠀", "PBB.BBBBBBBBBBB."),
)

# Every row is the same width; the header lays the mark out against this.
WIDTH = len(_LOGO[0][0])


def logo_lines(*, color: bool = True) -> list[str]:
    """The mark, one rendered string per row.

    Args:
        color: emit ANSI escapes. When ``False`` the glyphs come back bare.

    Returns:
        Eight strings, each ``WIDTH`` glyphs wide once escapes are stripped.
    """
    return [_row(chars, colors, color) for chars, colors in _LOGO]


def logo(*, color: bool = True) -> str:
    """The mark as one block of eight rows, each terminated by a newline."""
    return "".join(f"{line}\n" for line in logo_lines(color=color))


def _row(chars: str, colors: str, color: bool) -> str:
    """One grid row, collapsed into runs of equal colour tag."""
    out: list[str] = []
    start = 0
    for i in range(1, len(colors) + 1):
        if i == len(colors) or colors[i] != colors[start]:
            out.append(paint(chars[start:i], fg=_COLOR.get(colors[start]), enabled=color))
            start = i
    return "".join(out)
