"""``InlineEditRef`` -- text that reads as plain text and edits in place.

A title, a name, a key: shown as text, edited where it sits. The value is
the text and lives in the browser like every input (see ``input``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Write

from .input import InputLeaf, _common, _Placeholder, _Submits


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import StrArg

    from ..vocab import ControlSize


__all__ = ["InlineEditRef"]


class InlineEditRef(_Submits, _Placeholder, InputLeaf):
    """Text shown as plain text, edited in place. The value is the text.

    A click, Enter or Space opens the editor with the text selected. Enter
    saves and submits (a change when the text moved, then ``on_submit()``),
    a blur saves (a change when it moved), Escape cancels and puts the text
    back. The value lands when the edit is saved, so a read while the editor
    is open sees the saved text. A ``required`` one saved empty is a cancel.

    ``error`` is a line of error text under it, and turns the editor red;
    ``set_error("")`` clears it. Inside a ``Field`` the Field's error does
    the same. ``readonly`` shows the text and never opens the editor.
    ``placeholder`` shows, muted, while the text is empty.
    """

    _wire_type = "InlineEditRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        value: str = "",
        error: str = "",
        max_length: int | None = None,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            placeholder=placeholder,
            value=value,
            error=error,
            max_length=max_length,
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
        return Write(self, value)

    def set_error(self, text: StrArg) -> Nu:
        """Show an error under the text; an empty one clears it."""
        return Write(self, Dict.of(error=text))
