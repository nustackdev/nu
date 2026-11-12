"""Shared vocabulary of the widget kit: the Literals several Refs take, and the href write.

One spelling per idea, so a Button, a Link and a Card cannot drift apart on
what a target or a control size is. The kit's TS nodes read the same words.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, get_args

from nu.forms import Dict
from nu.lang import Nu
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write


if TYPE_CHECKING:
    from nu.lang.args import StrArg
    from nustd.ui.core import Ref


__all__ = [
    "ControlSize",
    "HeadingTone",
    "IconTone",
    "PageWidth",
    "StatusTone",
    "Target",
    "TextAlign",
    "Tone",
    "one_of",
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

#: A named page width, the kit's ``--container-*`` tokens: a form 480, reading
#: prose 640, a panel or detail view 960, a site's main column 1200, a wide
#: dashboard 1400. "full" is no cap. Every container size prop takes one
#: (a ``Length``, see ``collections.layout``).
PageWidth = Literal["form", "prose", "panel", "main", "dashboard", "full"]

#: Where text sits on its line, logical so it follows the writing direction.
TextAlign = Literal["start", "center", "end"]


def set_href(ref: Ref, url: StrArg, target: Target | StrArg = UNSET) -> Nu:
    """Point ``ref`` at ``url``, and say where it opens only when ``target`` is given.

    An empty url takes the link away, so a Button or a Card is plain again.
    """
    payload: dict[str, object] = {"href": url}
    if target is not UNSET:
        payload["target"] = target
    return Write(ref, Dict.of(**payload))


def one_of(owner: str, prop: str, value: object, choices: object) -> object:
    """``value`` when it is one of the Literal ``choices``, else fail loud with the list.

    A term (computed at run time) and ``UNSET`` pass as they are: only a value
    written in the program can be checked when it is built. The browser draws
    an unknown word as its default, so a typo here would draw wrong silently.
    """
    if value is UNSET or isinstance(value, Nu):
        return value
    allowed = get_args(choices)
    if value not in allowed:
        msg = f"{owner} {prop} is one of {', '.join(allowed)}, not {value!r}"
        raise ValueError(msg)
    return value
