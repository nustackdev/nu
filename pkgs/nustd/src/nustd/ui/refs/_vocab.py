"""Shared vocabulary of the widget kit: the Literals several Refs take, and the href write.

One spelling per idea, so a Button, a Link and a Card cannot drift apart on
what a target or a control size is. The kit's TS nodes read the same words.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import StrArg
    from nustd.ui.core import Ref


__all__ = [
    "Align",
    "ControlSize",
    "HeadingTone",
    "IconTone",
    "StatusTone",
    "Target",
    "TextAlign",
    "Tone",
    "set_href",
]


#: Where a link opens: this tab, or a new one.
Target = Literal["_self", "_blank"]

#: A control's height step (Button, Link drawn as a button): 20, 24, 32, 40 px.
ControlSize = Literal["xs", "sm", "md", "lg"]

#: Text ink. ``secondary`` and ``muted`` step back, the rest call a line out.
Tone = Literal["primary", "secondary", "muted", "accent", "danger", "warn", "ok", "info"]

#: An icon's ink: a text tone, or ``inherit`` for the color of the text around it.
IconTone = Literal["inherit", Tone]

#: A heading's ink. A heading never steps back as far as ``muted``.
HeadingTone = Literal["primary", "secondary", "accent"]

#: A live state's tone (a status dot, a status pill): neutral, or a status.
StatusTone = Literal["neutral", "info", "ok", "warn", "danger"]

#: Where a flex container places its children across its main axis.
Align = Literal["start", "center", "end", "stretch"]

#: Where text sits on its line. start / end are canonical, the way a Line
#: spells it; left / right still read.
TextAlign = Literal["start", "center", "end", "left", "right"]


def set_href(ref: Ref, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
    """Point ``ref`` at ``url``, and say where it opens only when ``target`` is given.

    An empty url takes the link away, so a Button or a Card is plain again.
    """
    payload: dict[str, object] = {"href": url}
    if target is not UNSET:
        payload["target"] = target
    return Write(ref, Dict.of(**payload))
