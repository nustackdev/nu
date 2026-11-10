"""``TimelineRef`` -- lanes of colored intervals over one time window.

Server-owned, display only: the server ships the window and the lanes, the
browser draws them. A write is a partial merge of props, so each setter sends
only what it names, and ``lanes`` is replaced whole::

    class Jobs(nustd.ui.Column):
        timeline = nustd.ui.TimelineRef.slot(noun="job", legend={"ok": "done", "danger": "failed"})

    Jobs.timeline.set(lanes, start=now - 3_600_000, end=now, total_lanes=240)

**A lane** is ``{title, icon, href, items}`` plus, optionally, ``id``,
``target`` and ``count``. ``icon`` is a lucide name or a short text drawn as
is (an emoji). With an ``href`` the label is a real link to the page.
``count`` is the lane's full count when fewer items were sent; it defaults to
the number of items. ``count_label`` words the count cell instead (``"100+
runs"``), for a caller that knows only a lower bound.

**An item** is an interval: ``(start, end, tone, label)``, the last two
optional, or a dict of the same keys. Times are epoch ms (like a chart's time
axis); a ``datetime`` in a literal is turned into ms here. ``end`` None is an
interval with no end yet, drawn to the window's end like any other bar.
``tone`` is a status tone (``neutral``, ``info``, ``ok``, ``warn``,
``danger``) and sets the bar's color; ``label`` leads its tooltip. An
interval too short to see is drawn at a minimum width. Overlapping items of
one lane pack into up to three sub-rows; past that they stack, translucent.

Capping is honest. Past ``max_lanes`` (10, 0 for no cap) the rest is one
"+N more" row, N counted from ``total_lanes`` when there are more lanes than
were sent. Past ``max_items`` (100) a lane draws its danger items first, then
its newest, and its count stays the full one.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write

from .base import LeafRef


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from nu.lang import Nu
    from nu.lang.args import DictArg, FloatArg, IntArg, ListArg, StrArg

    from ..vocab import StatusTone, Target


__all__ = ["TimelineRef"]


TimelineAxis = Literal["relative", "clock", "none"]

Time = float | int | datetime


def _ms(t: Any) -> Any:
    """A datetime as epoch ms; anything else rides as is."""
    return round(t.timestamp() * 1000) if isinstance(t, datetime) else t


def _normalize_item(item: Any) -> Any:
    if isinstance(item, (list, tuple)):
        out = [_ms(t) if i < 2 else t for i, t in enumerate(item)]
        if len(out) == 1:
            out.append(None)
        return out
    if isinstance(item, dict):
        return {**item, "start": _ms(item.get("start")), "end": _ms(item.get("end"))}
    return item


def _normalize_lanes(lanes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Tuples to lists and datetimes to ms, so a literal goes out as plain JSON."""
    out = []
    for lane in lanes:
        d = dict(lane)
        d["items"] = [_normalize_item(it) for it in d.get("items", ())]
        out.append(d)
    return out


class TimelineRef(LeafRef):
    """Lanes of colored intervals over a time window, an axis, a "+N more" row.

    Each lane is a page link on the left, its items as bars on a track, its
    count on the right. Hovering a bar shows its label, tone name, times and
    length.

    `axis` "relative" counts back from the end ("60m ago" .. "now"), "clock"
    shows wall times, "none" draws no axis. The window is any span, seconds
    to weeks; the ticks word themselves to fit ("15m", "2h 30m", "3d ago").
    `legend` names the tones in use (``{"ok": "done", "danger": "failed"}``)
    for the legend and the tooltips; unnamed tones go unlisted. `noun`
    names an item in the counts ("1 job", "48 jobs"; `noun_plural` when
    adding an s is wrong). `more_label` follows "+N" in the more row;
    `more_text` and `more_href` put a link there to see them all.
    `max_lanes` 0 draws every lane sent, for a caller that picks the lanes
    itself. `note` is a quiet line under the lanes.
    """

    _wire_type = "TimelineRef"

    @classmethod
    def slot(
        cls,
        *,
        start: Time = 0,
        end: Time = 0,
        lanes: Sequence[Mapping[str, Any]] | None = None,
        total_lanes: int = 0,
        max_lanes: int = 10,
        max_items: int = 100,
        noun: str = "item",
        noun_plural: str = "",
        axis: TimelineAxis = "relative",
        legend: Mapping[StatusTone, str] | None = None,
        more_label: str = "more",
        more_text: str = "",
        more_href: str = "",
        more_target: Target = "_self",
        note: str = "",
    ) -> Self:
        return super().slot(
            start=_ms(start),
            end=_ms(end),
            lanes=_normalize_lanes(lanes or []),
            total_lanes=total_lanes,
            max_lanes=max_lanes,
            max_items=max_items,
            noun=noun,
            noun_plural=noun_plural,
            axis=axis,
            legend=dict(legend or {}),
            more_label=more_label,
            more_text=more_text,
            more_href=more_href,
            more_target=more_target,
            note=note,
        )

    def set(
        self,
        lanes: ListArg[dict[str, Any]],
        start: FloatArg | datetime = UNSET,
        end: FloatArg | datetime = UNSET,
        total_lanes: IntArg = UNSET,
    ) -> Nu:
        """Ship the lanes whole; the window and the total change only when passed."""
        # A literal list is normalized here; a term rides as is.
        payload: dict[str, object] = {
            "lanes": _normalize_lanes(lanes) if isinstance(lanes, (list, tuple)) else lanes
        }
        if start is not UNSET:
            payload["start"] = _ms(start)
        if end is not UNSET:
            payload["end"] = _ms(end)
        if total_lanes is not UNSET:
            payload["total_lanes"] = total_lanes
        return Write(self, Dict.of(**payload))

    def set_window(self, start: FloatArg | datetime, end: FloatArg | datetime) -> Nu:
        """Move the window, the lanes as they are."""
        return Write(self, Dict.of(start=_ms(start), end=_ms(end)))

    def set_legend(self, names: DictArg[str, str]) -> Nu:
        """Rename the tones; a tone left out goes unlisted."""
        return Write(self, Dict.of(legend=names))

    def set_more(
        self,
        label: StrArg,
        text: StrArg = UNSET,
        href: StrArg = UNSET,
        target: Target | StrArg = UNSET,
    ) -> Nu:
        """Reword the more row; an empty text drops its link."""
        payload: dict[str, object] = {"more_label": label}
        if text is not UNSET:
            payload["more_text"] = text
        if href is not UNSET:
            payload["more_href"] = href
        if target is not UNSET:
            payload["more_target"] = target
        return Write(self, Dict.of(**payload))

    def set_note(self, text: StrArg) -> Nu:
        """The quiet line under the lanes; empty hides it."""
        return Write(self, Dict.of(note=text))
