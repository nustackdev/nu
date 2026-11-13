"""RangeSliderRef: a two-thumb slider whose ``[low, high]`` lives in the browser.

Its own Ref rather than ``SliderRef(range=True)``: the value is a pair, not a
number, so the seed, ``set``, a read and a Form's values all have one shape
per class, and ``SliderRef`` stays a float end to end.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write

from .input import InputLeaf, _common


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import BoolArg, FloatArg, ListArg, StrArg

    from ..vocab import ControlSize


#: A mark under the track: a value, ``(value, label)``, or ``{"value", "label"}``.
Mark = float | tuple[float, str] | Mapping[str, object]


def _pair(value: Sequence[float] | None, lo: float, hi: float) -> list[float]:
    """A literal seed as an ordered pair; ``None`` is the whole span."""
    if value is None:
        return [lo, hi]
    if isinstance(value, str) or len(value) != 2:
        raise ValueError(f"RangeSliderRef value is a [low, high] pair, got {value!r}")
    a, b = (float(x) for x in value)
    return [a, b] if a <= b else [b, a]


def _normalize_marks(marks: Sequence[Mark]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for m in marks:
        if isinstance(m, Mapping):
            mark: dict[str, object] = {"value": float(m["value"])}  # type: ignore[arg-type]
            if m.get("label") is not None:
                mark["label"] = str(m["label"])
            out.append(mark)
        elif isinstance(m, tuple):
            out.append({"value": float(m[0]), "label": str(m[1])})
        else:
            out.append({"value": float(m)})
    return out


class RangeSliderRef(InputLeaf):
    """Two-thumb slider whose ``[low, high]`` value lives in the browser.

    The value is a two-item list, low first; the thumbs cannot cross. A drag
    is local, the release (or an arrow key) commits, heard by ``on_change()``.
    No send key, so no ``on_submit()``. ``value=None`` seeds the whole span,
    ``[min, max]``. A write that is not a pair lands as ``[min, max]``; a
    pair is clamped to the bounds and put in order.

    ``marks`` label points under the track: numbers, ``(value, label)``
    pairs or ``{"value", "label"}`` maps. ``format`` is how a value reads in
    the readout and on an unlabelled mark, ``{}`` standing for the number
    rounded to ``step`` (``"{}%"``, ``"${}"``). ``thumb_labels`` names the
    two thumbs for screen readers; the label names the pair as a group.
    """

    _wire_type = "RangeSliderRef"

    @classmethod
    def slot(
        cls,
        *,
        min: float = 0.0,
        max: float = 100.0,
        step: float = 1.0,
        value: Sequence[float] | None = None,
        label: str = "",
        marks: Sequence[Mark] = (),
        format: str = "{}",
        show_value: bool = True,
        thumb_labels: tuple[str, str] = ("Minimum", "Maximum"),
        disabled: bool = False,
        readonly: bool = False,
        required: bool = False,
        autofocus: bool = False,
        size: ControlSize = "md",
    ) -> Self:
        return super().slot(
            min=min,
            max=max,
            step=step,
            value=_pair(value, min, max),
            marks=_normalize_marks(marks),
            format=format,
            show_value=show_value,
            thumb_labels=list(thumb_labels),
            **_common(
                label=label,
                disabled=disabled,
                readonly=readonly,
                required=required,
                autofocus=autofocus,
                size=size,
            ),
        )

    def set_min(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(min=value))

    def set_max(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(max=value))

    def set_step(self, value: FloatArg) -> Nu:
        return Write(self, Dict.of(step=value))

    def set_marks(self, marks: Sequence[Mark]) -> Nu:
        return Write(self, Dict.of(marks=_normalize_marks(marks)))

    def set_format(self, template: StrArg) -> Nu:
        return Write(self, Dict.of(format=template))

    def set_show_value(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(show_value=flag))

    def set(
        self,
        value: ListArg[float] | Sequence[float],
        min: FloatArg = UNSET,
        max: FloatArg = UNSET,
        step: FloatArg = UNSET,
        label: StrArg = UNSET,
    ) -> Nu:
        """Write the pair; with bounds, write them in the same frame."""
        if isinstance(value, tuple):
            value = list(value)
        if all(x is UNSET for x in (min, max, step, label)):
            return Write(self, value)
        payload: dict[str, object] = {"value": value}
        if min is not UNSET:
            payload["min"] = min
        if max is not UNSET:
            payload["max"] = max
        if step is not UNSET:
            payload["step"] = step
        if label is not UNSET:
            payload["label"] = label
        return Write(self, Dict.of(**payload))
