"""ColorPickerRef: a color input whose ``#rrggbb`` value lives in the browser."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Write

from .input import InputLeaf, _common, _Submits


if TYPE_CHECKING:
    from collections.abc import Sequence

    from nu.lang import Nu
    from nu.lang.args import BoolArg, StrArg

    from ..vocab import ControlSize


#: The kit chart palette, read off the theme tokens in the browser.
Palette = Literal["palette"]

_HEX6 = re.compile(r"^#?([0-9a-fA-F]{6})$")
_HEX3 = re.compile(r"^#?([0-9a-fA-F]{3})$")


def normalize_hex(raw: str) -> str:
    """``#abc``, ``ABCDEF`` or ``#aabbcc`` as lowercase ``#aabbcc``. Raises on anything else."""
    s = raw.strip()
    if m := _HEX6.match(s):
        return f"#{m.group(1).lower()}"
    if m := _HEX3.match(s):
        return "#" + "".join(c * 2 for c in m.group(1).lower())
    raise ValueError(f"not a hex color: {raw!r}")


def _swatches(swatches: Sequence[str] | Palette | None) -> list[str] | str | None:
    if swatches is None:
        return None
    if swatches == "palette":
        return "palette"
    if isinstance(swatches, str):
        raise ValueError(f'swatches is a list of hex colors or "palette", got {swatches!r}')
    return [normalize_hex(s) for s in swatches]


class ColorPickerRef(_Submits, InputLeaf):
    """Color input whose ``#rrggbb`` value lives in the browser.

    A swatch trigger opens a popover with a saturation and brightness area, a
    hue slider, a hex field and the optional ``swatches``. A drag commits on
    release, a swatch at once, the hex field on blur, each heard by
    ``on_change()``. Enter in the hex field (or on the closed trigger) submits,
    heard by ``on_submit()``. ``value=`` takes ``#abc`` or ``#aabbcc`` in any
    case and reads back as lowercase ``#aabbcc``; a write that is not a hex
    keeps the color the picker had.

    ``swatches`` is a list of hex colors, or ``"palette"`` for the kit's
    chart palette in the theme the picker opens in. ``show_hex=False`` draws
    the trigger as the swatch alone.
    """

    _wire_type = "ColorPickerRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        value: str = "#000000",
        swatches: Sequence[str] | Palette | None = None,
        show_hex: bool = True,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            value=normalize_hex(value),
            swatches=_swatches(swatches),
            show_hex=bool(show_hex),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: StrArg) -> Nu:
        """Write the color.

        A hex literal is folded here; anything else the browser folds, or keeps
        the color it had when it is not a hex.
        """
        if isinstance(value, str) and (_HEX6.match(value.strip()) or _HEX3.match(value.strip())):
            value = normalize_hex(value)
        return Write(self, value)

    def set_swatches(self, swatches: Sequence[str] | Palette | None) -> Nu:
        return Write(self, Dict.of(swatches=_swatches(swatches)))

    def set_show_hex(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(show_hex=flag))
