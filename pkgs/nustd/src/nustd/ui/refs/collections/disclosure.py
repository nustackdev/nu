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

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import Self, Unpack

from nu.forms import Dict
from nu.lang.sentinels import UNSET
from nustd.ui.core.interactions import Changed, Write

from .base import DictCollectionRef
from .flow import FLOW_CHILDREN, STACK
from .layout import ChildLayout, StackLayout, one_of


if TYPE_CHECKING:
    from nu.domains.shape import Slot
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


class CollapsibleRef(ChildLayout, DictCollectionRef):
    """One titled region whose children fold away.

    A trigger row (chevron + title) over a body of open-ended children. The
    user toggles it in the tab, which sends ``{open: bool}`` as a notify;
    ``on_change()`` takes those. ``set(open=...)`` opens or closes it from
    the server. The body speaks the layers of a Column (``layout``):
    ``gap`` (3), ``padding``, ``justify``, ``align``, ``divided``, and the
    per child maps.
    """

    _wire_type = "Collapsible"
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        title: str = "",
        open: bool = False,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(item, title=title, open=bool(open), **cls._laid_out(layout))

    def set_open(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        return Write(self, Dict.of(**_open_title(open, title)))

    def on_change(self) -> Changed:
        return Changed(self)


Side = Literal["left", "right", "top", "bottom"]
_SIDES = ("left", "right", "top", "bottom")


class SheetRef(ChildLayout, DictCollectionRef):
    """Drawer that slides in from an edge over the page, children as its body.

    Server-owned ``open`` and ``title``. When ``dismissible`` is true the user
    can close it (backdrop, Esc, the close button) and the tab sends
    ``{open: false}``, which ``on_change()`` takes. Like Modal, the sheet
    stays open until the program writes ``open=False`` back, so a program
    can hold it open (unsaved edits).

    A left or right sheet is ``width`` wide (440px unless set), a top or
    bottom one ``height`` tall (320px unless set). The body speaks the
    layers of a Column (``layout``): ``gap`` (4), ``padding``, ``justify``,
    ``align``, ``divided``, and the per child maps.
    """

    _wire_type = "Sheet"
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        open: bool = False,
        title: str = "",
        side: Side = "right",
        dismissible: bool = True,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(
            item,
            open=bool(open),
            title=title,
            side=one_of("SheetRef", "side", side, _SIDES),
            dismissible=bool(dismissible),
            **cls._laid_out(layout),
        )

    def set_open(self, flag: BoolArg) -> Nu:
        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        return Write(self, Dict.of(**_open_title(open, title)))

    def on_change(self) -> Changed:
        return Changed(self)
