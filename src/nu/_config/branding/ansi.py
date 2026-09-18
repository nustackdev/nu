"""Minimal ANSI SGR helpers -- the brand kit's whole rendering layer.

Stdlib only, on purpose: the brand kit lives in the kernel now, and the
kernel takes no dependency beyond ``typing-extensions`` and ``cloudpickle``.
Everything here is a plain string transform.

Two rules govern whether escapes are emitted at all:

- ``NO_COLOR`` set to a non-empty value disables them (https://no-color.org).
- the target stream must be a tty; piping ``nu`` into a file or a pager
  must never leak escape junk.

Attribute order in the emitted sequence matches what rich produced before
(bold, dim, underline, then the truecolor foreground) so terminal output is
byte-identical to the previous rich-rendered brand kit.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import IO


__all__ = ["RESET", "color_enabled", "paint"]

RESET = "\x1b[0m"


def color_enabled(stream: IO[str] | None = None) -> bool:
    """Whether ``stream`` should get ANSI escapes.

    Args:
        stream: the destination. Defaults to ``sys.stdout``.

    Returns:
        ``True`` only when ``NO_COLOR`` is unset/empty and the stream is a
        tty. A stream that raises or has no ``isatty`` counts as not a tty.
    """
    if os.environ.get("NO_COLOR"):
        return False
    stream = sys.stdout if stream is None else stream
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """``"#7a4ce0"`` -> ``(122, 76, 224)``."""
    value = color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def paint(
    text: str,
    *,
    fg: str | None = None,
    bold: bool = False,
    dim: bool = False,
    underline: bool = False,
    enabled: bool = True,
) -> str:
    """Wrap ``text`` in one SGR sequence, or return it untouched.

    Args:
        text: the string to style.
        fg: foreground as a ``#rrggbb`` hex string, or ``None``.
        bold: emit SGR 1.
        dim: emit SGR 2.
        underline: emit SGR 4.
        enabled: when ``False``, or when no attribute is requested, ``text``
            comes back unchanged with no escapes at all.

    Returns:
        The styled string, always terminated by a reset when styled.
    """
    if not enabled or not text:
        return text
    codes: list[str] = []
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    if underline:
        codes.append("4")
    if fg is not None:
        r, g, b = _hex_to_rgb(fg)
        codes.append(f"38;2;{r};{g};{b}")
    if not codes:
        return text
    return f"\x1b[{';'.join(codes)}m{text}{RESET}"
