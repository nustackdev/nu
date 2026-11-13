"""Date and time input Refs: a time of day, a date with a time, a span of days.

Siblings of ``DatePickerRef`` (in ``input``), on the same contract
(``InputLeaf``): the value lives in the browser, ``value=`` seeds it, ``set``
writes it, ``reset`` puts the seed back, ``on_change`` hears each committed
change and ``on_submit`` hears Enter. Values are local ISO strings, never
timezone-shifted: ``"HH:MM"`` for a time, ``"YYYY-MM-DDTHH:MM"`` for a date
and time, ``{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}`` for a range. An
empty part reads ``""``.

Each is clearable by default: a clear button sits in the field while it holds
a value, and clearing is a change.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write

from .input import InputLeaf, _common, _Nullable, _Placeholder, _Submits


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import StrArg

    from ..vocab import ControlSize


def _time(value: str | dt.time, *, seconds: bool = False) -> str:
    """A time of day as "HH:MM" (or "HH:MM:SS"); strings pass through."""
    if isinstance(value, dt.time):
        return value.strftime("%H:%M:%S" if seconds or value.second else "%H:%M")
    return value


def _date_time(value: str | dt.datetime | dt.date) -> str:
    """A local date and time as "YYYY-MM-DDTHH:MM"; a bare date is midnight; strings pass through."""
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%dT%H:%M")
    if isinstance(value, dt.date):
        return f"{value.isoformat()}T00:00"
    return value


def _date(value: str | dt.date | None) -> str:
    """A date as "YYYY-MM-DD"; None is ""; strings pass through."""
    if value is None:
        return ""
    if isinstance(value, dt.date):
        return value.isoformat()
    return value


class TimePickerRef(_Nullable, _Submits, InputLeaf):
    """Time of day input whose "HH:MM" value lives in the browser (NULL for none).

    The field is typed into, segment by segment: blur commits (a change, when
    the time moved), Enter commits and submits. The clear button is a change
    too. `step` is in seconds: under 60 the value carries seconds,
    "HH:MM:SS". `min` and `max` bound the time the browser takes as valid.
    """

    _wire_type = "TimePickerRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        value: str | dt.time | None = None,
        min: str | dt.time = "",
        max: str | dt.time = "",
        step: int | None = None,
        clearable: bool = True,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        seconds = step is not None and step < 60
        return super().slot(
            value=_time(value, seconds=seconds) if value else None,
            min=_time(min, seconds=seconds),
            max=_time(max, seconds=seconds),
            step=step,
            clearable=bool(clearable),
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


class DateTimePickerRef(_Nullable, _Submits, _Placeholder, InputLeaf):
    """Date and time input whose "YYYY-MM-DDTHH:MM" value lives in the browser (NULL for none).

    A calendar pick is a change at once and keeps the time already there
    (midnight when there is none). The time field beside it is typed into:
    blur commits. Enter on the closed date picker or in the time field
    submits. `min` and `max` are ISO date-times: days outside them are
    disabled, and on the first or last day the time takes the bound.
    """

    _wire_type = "DateTimePickerRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        value: str | dt.datetime | dt.date | None = None,
        min: str | dt.datetime | dt.date = "",
        max: str | dt.datetime | dt.date = "",
        clearable: bool = True,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            placeholder=placeholder,
            value=_date_time(value) if value else None,
            min=_date_time(min),
            max=_date_time(max),
            clearable=bool(clearable),
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


class DateRangePickerRef(_Submits, _Placeholder, InputLeaf):
    """Span of days whose ``{"start", "end"}`` value lives in the browser.

    Each end is an ISO "YYYY-MM-DD", "" while unset. Picks in the open
    calendar (the first click starts the range, the second ends it) commit
    when the calendar closes: a change, when the range moved. Enter on the
    closed picker submits; the clear button (or Backspace on it) empties
    the range, a change. `min` and `max` bound the days on offer.

    ``set`` takes the range as a mapping, ``set({"start": a, "end": b})``,
    or its two ends, ``set(start=a, end=b)``, each any string term.
    """

    _wire_type = "DateRangePickerRef"

    @classmethod
    def slot(
        cls,
        *,
        label: str = "",
        placeholder: str = "",
        value: dict[str, str | dt.date | None] | None = None,
        min: str | dt.date = "",
        max: str | dt.date = "",
        clearable: bool = True,
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        given = value or {}
        return super().slot(
            placeholder=placeholder,
            value={"start": _date(given.get("start")), "end": _date(given.get("end"))},
            min=_date(min),
            max=_date(max),
            clearable=bool(clearable),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set(self, value: Any = UNSET, *, start: StrArg = UNSET, end: StrArg = UNSET) -> Nu:  # type: ignore[override]
        if value is UNSET:
            value = Dict.of(start="" if start is UNSET else start, end="" if end is UNSET else end)
        return Write(self, Dict.of(value=value))
