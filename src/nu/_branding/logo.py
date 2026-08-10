"""Nu mark rendered as terminal braille glyphs.

Compact 2x4 sub-pixel braille packing of the SVG mark -- two interlocking
glyphs, purple top-left and blue bottom-right matching the SVG gradient
stops.

Baked once from the source PNG so this module has zero runtime deps beyond
rich + stdlib.
"""

from __future__ import annotations

from rich.text import Text

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


def logo() -> Text:
    """Return the Nu mark as a coloured rich ``Text``."""
    out = Text()
    for chars, colors in _LOGO:
        run_start = 0
        run_color = colors[0]
        for i in range(1, len(colors)):
            if colors[i] != run_color:
                _append_run(out, chars, run_start, i, run_color)
                run_start = i
                run_color = colors[i]
        _append_run(out, chars, run_start, len(colors), run_color)
        out.append("\n")
    return out


def _append_run(text: Text, chars: str, start: int, end: int, color: str) -> None:
    segment = chars[start:end]
    style = _COLOR.get(color)
    text.append(segment, style=style) if style else text.append(segment)
