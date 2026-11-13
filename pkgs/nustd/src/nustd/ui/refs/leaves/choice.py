"""Choice inputs: picks over a list of options, plus free text with suggestions.

- ``SegmentedControlRef``: one pick from a joined row of buttons.
- ``CheckboxGroupRef``: several picks from a list of checkboxes.
- ``MultiSelectRef``: several picks from a dropdown with a search field.
- ``AutocompleteRef``: any text, with suggestions from the options.

Each follows the input contract in ``input.py``: ``value=`` seeds it, ``set``
writes it, ``reset`` puts the seed back, ``on_change`` hears each committed
change, and the common props come with their setters. Options are strings
or ``{"value", "label"}`` dicts, as on ``SelectRef``, and ``set_options``
replaces them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Self

from nustd.ui.core import Write

from .input import (
    InputLeaf,
    Orientation,
    _common,
    _normalize_options,
    _options_write,
    _Placeholder,
    _Submits,
)


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import ListArg, StrArg

    from ..vocab import ControlSize


Options = list[str] | list[dict[str, str]]


class SegmentedControlRef(InputLeaf):
    """One pick from a joined row of buttons (``Day | Week | Month``).

    The value is the picked option's value ("" for none), live in the
    browser. A pick (a click, or an arrow key moving along the row) commits
    at once and is heard by ``on_change``. Same options and value as
    ``RadioGroupRef``; reach for it when the choices are few and short and
    belong in one row, a range or a view switch. ``fill=True`` stretches the
    row over the width it is given. `label` names the group (or the Field
    around it does).
    """

    _wire_type = "SegmentedControlRef"

    @classmethod
    def slot(
        cls,
        *,
        options: Options | None = None,
        value: str = "",
        fill: bool = False,
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            value=value,
            fill=bool(fill),
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

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        return _options_write(self, opts)


class CheckboxGroupRef(InputLeaf):
    """Several picks from a list of checkboxes.

    The value is the list of ticked option values, in option order ([] for
    none), live in the browser. Each tick commits at once and is heard by
    ``on_change``. ``set`` takes a list (a lone string ticks just that one).
    `label` names the group (or the Field around it does).
    """

    _wire_type = "CheckboxGroupRef"

    @classmethod
    def slot(
        cls,
        *,
        options: Options | None = None,
        value: list[str] | None = None,
        orientation: Orientation = "vertical",
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            value=list(value or []),
            orientation=orientation,
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: ListArg[str] | StrArg) -> Nu:
        return Write(self, value)

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        return _options_write(self, opts)


class MultiSelectRef(_Placeholder, InputLeaf):
    """Several picks from a dropdown with a search field.

    The value is the list of picked option values, in option order ([] for
    none), live in the browser. Each pick in the open list ticks one option
    on or off, commits at once and is heard by ``on_change``; the list stays
    open for the next. ``set`` takes a list (a lone string picks just that
    one). The searchable sibling of ``CheckboxGroupRef``, for long lists.
    """

    _wire_type = "MultiSelectRef"

    @classmethod
    def slot(
        cls,
        *,
        options: Options | None = None,
        value: list[str] | None = None,
        placeholder: str = "",
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            value=list(value or []),
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

    def set(self, value: ListArg[str] | StrArg) -> Nu:
        return Write(self, value)

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        return _options_write(self, opts)


class AutocompleteRef(_Submits, _Placeholder, InputLeaf):
    """Text input with a suggestion list; any text is a value.

    The value is the text, live in the browser, as on ``InputRef``: typing
    commits on blur, Enter commits and submits (``on_submit``). The list
    under the field offers the options that match what is typed. Enter on a
    highlighted suggestion (arrow keys move the highlight) or a click on one
    puts its value in the field and commits at once, with no submit.
    ``set_options`` swaps the suggestions, say as the person types.
    """

    _wire_type = "AutocompleteRef"

    @classmethod
    def slot(
        cls,
        *,
        options: Options | None = None,
        value: str = "",
        placeholder: str = "",
        clear_on_submit: bool = False,
        label: str = "",
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            options=_normalize_options(options or []),
            value=value,
            placeholder=placeholder,
            clear_on_submit=bool(clear_on_submit),
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

    def set_options(self, opts: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        return _options_write(self, opts)
