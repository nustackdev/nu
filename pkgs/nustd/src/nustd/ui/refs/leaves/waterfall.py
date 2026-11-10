"""WaterfallRef -- spans on one shared time axis, like a trace view.

A span is a dict of ``{id, label, start, end, tone, parent, detail}``. Times
are numbers in ms, epoch or relative (a ``datetime`` is turned into epoch ms);
the axis reads offsets from the window start. ``end`` of ``None`` is a span
still running, drawn up to ``now``. ``parent`` names the span it runs inside;
spans without one read as a sequence. ``tone`` is the status tone
(neutral, info, ok, warn, danger).

Past ``max_rows`` the browser draws one row counting the rest, failures
apart: no span is dropped without a number. With ``selectable``, a row click
marks it selected and ``on_select()`` gets ``{event, id, label, start, end,
tone, parent}``.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from nu.forms import Dict
from nustd.ui.core import Changed, Write

from .base import LeafRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import BoolArg, FloatArg, IntArg, ListArg, StrArg


__all__ = ["WaterfallRef"]


Span = Mapping[str, Any]


def _ms(v: object) -> float | None:
    if isinstance(v, datetime):
        return v.timestamp() * 1000
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v)


def _arg_ms(v: Any) -> Any:
    """A literal time as ms; a term rides as is."""
    return _ms(v) if v is None or isinstance(v, (int, float, datetime)) else v


def _normalize_spans(spans: object) -> list[dict[str, object]]:
    """Each span as the browser reads it. A span with no number for ``start`` is skipped."""
    if not isinstance(spans, (list, tuple)):
        return []
    out: list[dict[str, object]] = []
    for i, s in enumerate(spans):
        if not isinstance(s, Mapping):
            continue
        start = _ms(s.get("start"))
        if start is None:
            continue
        span: dict[str, object] = {
            "id": str(s["id"]) if s.get("id") not in (None, "") else str(i),
            "label": "" if s.get("label") is None else str(s["label"]),
            "start": start,
            "end": _ms(s.get("end")),
        }
        for key in ("tone", "parent", "detail"):
            if s.get(key) not in (None, ""):
                span[key] = str(s[key])
        out.append(span)
    return out


class WaterfallRef(LeafRef):
    """Spans on one time axis, nested by ``parent``, capped at ``max_rows``.

    ``start`` / ``end`` fix the window (ms); ``None`` fits it to the spans.
    ``now`` is where running spans stop. ``label_width`` is the label column
    in px.
    """

    _wire_type = "WaterfallRef"

    @classmethod
    def slot(
        cls,
        *,
        spans: list[Span] | None = None,
        start: float | None = None,
        end: float | None = None,
        now: float | None = None,
        max_rows: int = 50,
        label_width: int = 200,
        selectable: bool = False,
        selected: str = "",
    ) -> Self:
        return super().slot(
            spans=_normalize_spans(spans or []),
            start=_ms(start),
            end=_ms(end),
            now=_ms(now),
            max_rows=int(max_rows),
            label_width=int(label_width),
            selectable=selectable,
            selected=selected,
        )

    def set(self, spans: ListArg[Span]) -> Nu:
        # A literal list is normalized here; a term rides as is and the
        # browser skips what it cannot read.
        data = _normalize_spans(spans) if isinstance(spans, (list, tuple)) else spans
        return Write(self, Dict.of(spans=data))

    def set_window(self, start: FloatArg | None, end: FloatArg | None) -> Nu:
        """Fix the window in ms; ``None`` on either side fits it to the spans."""
        return Write(self, Dict.of(start=_arg_ms(start), end=_arg_ms(end)))

    def set_now(self, now: FloatArg | None) -> Nu:
        """Where running spans stop, in ms; ``None`` is the window end."""
        return Write(self, Dict.of(now=_arg_ms(now)))

    def set_max_rows(self, n: IntArg) -> Nu:
        return Write(self, Dict.of(max_rows=n))

    def set_selectable(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(selectable=flag))

    def set_selected(self, span_id: StrArg) -> Nu:
        return Write(self, Dict.of(selected=span_id))

    # --- browser -> server ---------------------------------------------------

    def on_select(self) -> Changed:
        """``{event, id, label, start, end, tone, parent}``: a span row clicked."""
        return Changed(self, "select")
