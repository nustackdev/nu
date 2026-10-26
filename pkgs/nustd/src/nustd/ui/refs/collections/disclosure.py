"""Disclosure containers -- a region that opens and closes over its children.

- ``CollapsibleRef``: one titled region that folds, simpler than Accordion.
  The tab owns open state while the user clicks (like Accordion) and sends a
  notify on each toggle; the server can still open or close it.
- ``SheetRef``: an edge drawer, Modal's sibling for inspectors and side
  panels. The server owns open state; the tab sends ``{open: false}`` when
  the user dismisses it.

Open vs closed is the thing each one carries, so each has a ``set()`` for
it, the way Modal does. Every other child is open-ended composition: build
it as a slot on the Shape or as a Ref with ``parent_ref=`` this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core.interactions import Changed, Write

from .base import DictCollectionRef


if TYPE_CHECKING:
    from nu.lang import Nu
    from nu.lang.args import BoolArg, StrArg
    from nustd.ui.core import Ref, Section


__all__ = ["CollapsibleRef", "SheetRef"]


def _open_title(open: object, title: object) -> dict[str, object]:
    """The partial chrome payload ``set()`` writes: only what was passed."""
    payload: dict[str, object] = {}
    if open is not UNSET:
        payload["open"] = open
    if title is not UNSET:
        payload["title"] = title
    return payload


class CollapsibleRef(DictCollectionRef):
    """One titled region whose children fold away.

    A trigger row (chevron + title) over a body of open-ended children. The
    user toggles it in the tab, which sends ``{open: bool}`` as a notify;
    ``on_change()`` takes those. ``set(open=...)`` opens or closes it from
    the server.
    """

    _wire_type = "Collapsible"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        title: str = "",
        open: bool = False,
    ) -> Self:
        return super().slot(item, title=title, open=bool(open))

    def set_open(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        return Write(self, Dict.of(**_open_title(open, title)))

    def on_change(self) -> Changed:
        return Changed(self)


Side = Literal["left", "right", "top", "bottom"]
SheetSize = Literal["sm", "md", "lg"]


class SheetRef(DictCollectionRef):
    """Drawer that slides in from an edge over the page, children as its body.

    Server-owned ``open`` and ``title``. When ``dismissible`` is true the user
    can close it (backdrop, Esc, the close button) and the tab sends
    ``{open: false}``, which ``on_change()`` takes. Like Modal, the sheet
    stays open until the program writes ``open=False`` back, so a program
    can hold it open (unsaved edits). ``size`` is the width of a left or
    right sheet and the height of a top or bottom one.
    """

    _wire_type = "Sheet"

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | None = None,
        /,
        *,
        open: bool = False,
        title: str = "",
        side: Side = "right",
        size: SheetSize = "md",
        dismissible: bool = True,
    ) -> Self:
        return super().slot(
            item,
            open=bool(open),
            title=title,
            side=side,
            size=size,
            dismissible=bool(dismissible),
        )

    def set_open(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        return Write(self, Dict.of(**_open_title(open, title)))

    def on_change(self) -> Changed:
        return Changed(self)
