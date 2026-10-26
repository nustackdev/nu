"""Display leaves -- small status and identity marks.

Server-owned sinks like the content leaves: the server pushes props with
``write``, the browser only renders. A write is a partial merge of props, so
each setter sends just the keys it names. Every Ref here is a ``LeafRef``.

- ``AvatarRef``: an image or initials for a person or thing.
- ``BreadcrumbRef``: the trail to here; the crumbs are data, not children.
- ``SkeletonRef``: a loading placeholder for a cell that fetches.
- ``SpinnerRef``: busy with no known progress (``ProgressRef`` covers known).
- ``StatusPillRef``: icon + label status that reads without color.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core import Write

from .base import LeafRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import IntArg, ListArg, StrArg

    from ..vocab import StatusTone


__all__ = ["AvatarRef", "BreadcrumbRef", "SkeletonRef", "SpinnerRef", "StatusPillRef"]


Size = Literal["sm", "md", "lg", "xl"]


class AvatarRef(LeafRef):
    """An image for a person or thing, initials from `name` when it has none.

    `src` is the image url; while it loads, or when it fails, the avatar
    shows up to two initials from `name`. `name` is also what a screen reader
    announces. `size` runs 24, 32, 40 and 48 px.
    """

    _wire_type = "AvatarRef"

    @classmethod
    def slot(cls, *, src: str = "", name: str = "", size: Size = "md") -> Self:
        return super().slot(src=src, name=name, size=size)

    def set_src(self, url: StrArg) -> Nu:
        return Write(self, Dict.of(src=url))

    def set_name(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(name=text))

    def set_size(self, name: Size | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set(
        self,
        src: StrArg,
        *,
        name: StrArg = UNSET,
        size: Size | StrArg = UNSET,
    ) -> Nu:
        payload: dict[str, object] = {"src": src}
        if name is not UNSET:
            payload["name"] = name
        if size is not UNSET:
            payload["size"] = size
        return Write(self, Dict.of(**payload))


def _normalize_crumbs(items: object) -> list[dict[str, str]]:
    """Accept ["Home", "Docs"] or [{"label": "Home", "href": "/"}] and return the dict form.

    A crumb's ``target`` rides along only when it names one, so a trail with
    none keeps its two-key crumbs.
    """
    if not isinstance(items, (list, tuple)):
        return []
    out: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, str):
            out.append({"label": item, "href": ""})
        elif isinstance(item, dict):
            label = "" if item.get("label") is None else str(item["label"])
            href = "" if item.get("href") is None else str(item["href"])
            crumb = {"label": label, "href": href}
            if item.get("target") is not None:
                crumb["target"] = str(item["target"])
            out.append(crumb)
    return out


class BreadcrumbRef(LeafRef):
    """The trail to here, as crumbs of `{label, href}`, and `target` per crumb.

    The last crumb is the current page and is not a link; a crumb with no
    `href` reads as plain text. A plain string is a crumb with that label and
    no link. An href on another host gets the external mark, like `LinkRef`.
    A crumb opens in this tab unless its `target` is "_blank".
    """

    _wire_type = "BreadcrumbRef"

    @classmethod
    def slot(cls, *, items: list[str] | list[dict[str, str]] | None = None) -> Self:
        return super().slot(items=_normalize_crumbs(items or []))

    def set(self, items: ListArg[str] | ListArg[dict[str, str]]) -> Nu:
        # A literal list is normalized here; a term rides as is and the
        # browser reads strings and dicts alike.
        crumbs = _normalize_crumbs(items) if isinstance(items, (list, tuple)) else items
        return Write(self, Dict.of(items=crumbs))


SkeletonShape = Literal["text", "rect", "circle"]


class SkeletonRef(LeafRef):
    """A pulsing placeholder where content is still loading.

    `text` draws `lines` bars of text height, the last one shorter. `rect` is
    one block `height` px tall (96 when 0). `circle` is a disc `height` px
    across (40 when 0), for an avatar to come. Text and rect take the width
    they are given; a circle keeps its size. No primary value, so no `set()`.
    """

    _wire_type = "SkeletonRef"

    @classmethod
    def slot(cls, *, lines: int = 1, shape: SkeletonShape = "text", height: int = 0) -> Self:
        return super().slot(lines=int(lines), shape=shape, height=int(height))

    def set_lines(self, n: IntArg) -> Nu:
        return Write(self, Dict.of(lines=n))

    def set_shape(self, name: SkeletonShape | StrArg) -> Nu:
        return Write(self, Dict.of(shape=name))

    def set_height(self, px: IntArg) -> Nu:
        return Write(self, Dict.of(height=px))


class SpinnerRef(LeafRef):
    """Busy with no known progress; `ProgressRef` covers known progress.

    `label` says what it is busy with, next to the spinner and as its
    accessible name ("Loading" when empty). `size` runs 14, 16, 20 and 24 px.
    """

    _wire_type = "SpinnerRef"

    @classmethod
    def slot(cls, *, size: Size = "md", label: str = "") -> Self:
        return super().slot(size=size, label=label)

    def set_size(self, name: Size | StrArg) -> Nu:
        return Write(self, Dict.of(size=name))

    def set(self, label: StrArg) -> Nu:
        return Write(self, Dict.of(label=label))


class StatusPillRef(LeafRef):
    """A state as icon + label, so it reads without color.

    Each tone draws its own icon (a triangle for `danger`, a check for `ok`,
    an info mark for `warn` and `info`, a ring for `neutral`), so the state
    survives color blindness and grayscale. Unlike `BadgeRef`, which tags,
    a pill says what state something is in.
    """

    _wire_type = "StatusPillRef"

    @classmethod
    def slot(cls, *, tone: StatusTone = "neutral", label: str = "") -> Self:
        return super().slot(tone=tone, label=label)

    def set_label(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(label=text))

    def set_tone(self, name: StatusTone | StrArg) -> Nu:
        return Write(self, Dict.of(tone=name))

    def set(self, label: StrArg, *, tone: StatusTone | StrArg = UNSET) -> Nu:
        # Tone first in the payload when given, as `StatusDotRef` ships it.
        payload: dict[str, object] = {}
        if tone is not UNSET:
            payload["tone"] = tone
        payload["label"] = label
        return Write(self, Dict.of(**payload))
