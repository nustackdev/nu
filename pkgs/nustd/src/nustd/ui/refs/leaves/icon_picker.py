"""IconPickerRef: an icon input whose stored icon string lives in the browser."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, get_args

from typing_extensions import Self

from nustd.ui.core import Write

from .input import InputLeaf, _common, _Placeholder


if TYPE_CHECKING:
    from collections.abc import Sequence

    from nu.lang import Nu
    from nu.lang.args import BoolArg, StrArg

    from ..vocab import ControlSize


#: The picker's tabs: the emoji set, and the kit's pack of lucide glyphs.
IconKind = Literal["emoji", "lucide"]

_KINDS: tuple[str, ...] = get_args(IconKind)

LUCIDE = "lucide:"
EMOJI = "emoji:"


def _kebab(name: str) -> str:
    """``FileText``, ``fileText`` and ``file-text`` are one name; so are ``Gamepad2`` and ``gamepad-2``."""
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name.strip())
    return re.sub(r"([a-zA-Z])(\d)", r"\1-\2", name).lower()


def normalize_icon(raw: str) -> str:
    """A stored icon in its one spelling, ``""`` for none. Raises on another prefix.

    ``"lucide:<name>"`` and a bare name are a lucide glyph, its name folded to
    lucide's kebab case; ``"emoji:<char>"`` is an emoji. Whether lucide has
    the name is the browser's to know: one it lacks reads there as no icon.
    """
    value = raw.strip()
    if not value:
        return ""
    if value.startswith(EMOJI):
        char = value[len(EMOJI) :].strip()
        if not char:
            raise ValueError(f"no emoji after {EMOJI!r}: {raw!r}")
        return f"{EMOJI}{char}"
    name = value[len(LUCIDE) :] if value.startswith(LUCIDE) else value
    if ":" in name or not name.strip():
        raise ValueError(f'an icon is "lucide:<name>", "emoji:<char>" or a bare name, got {raw!r}')
    return f"{LUCIDE}{_kebab(name)}"


def _kinds(kinds: Sequence[IconKind]) -> list[str]:
    out: list[str] = []
    for k in kinds:
        if k not in _KINDS:
            raise ValueError(f"icon kinds are {', '.join(_KINDS)}, not {k!r}")
        if k not in out:
            out.append(k)
    if not out:
        raise ValueError("an icon picker offers at least one kind")
    return out


class IconPickerRef(_Placeholder, InputLeaf):
    """Icon input whose stored icon string lives in the browser (``""`` for none).

    A trigger shows the icon and opens the kit icon picker: emoji and a pack of
    lucide glyphs, searched, picked from a grid, a bottom sheet on a phone. A
    pick lands and is heard by ``on_change()`` at once, the way a select's is;
    "Remove" (while ``clearable``) clears it the same way.

    The value is ``"lucide:<name>"`` or ``"emoji:<char>"``. ``value=`` and
    ``set()`` also take a bare lucide name in any case (``"FileText"`` reads
    back ``"lucide:file-text"``); a write the browser cannot read as an icon
    keeps the icon it had, and ``""`` clears. ``kinds`` picks the tabs and
    their order. ``placeholder`` is what the trigger says with no icon.
    """

    _wire_type = "IconPickerRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        value: str = "",
        kinds: Sequence[IconKind] = ("emoji", "lucide"),
        clearable: bool = True,
        placeholder: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            value=normalize_icon(value),
            kinds=_kinds(kinds),
            clearable=bool(clearable),
            placeholder=placeholder,
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
        """Write the icon.

        A literal is folded here (and fails loud when it is no icon); anything
        else the browser folds, or keeps the icon it had.
        """
        if isinstance(value, str):
            value = normalize_icon(value)
        return Write(self, value)

    def set_kinds(self, kinds: Sequence[IconKind]) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(kinds=_kinds(kinds)))

    def set_clearable(self, flag: BoolArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(clearable=flag))
