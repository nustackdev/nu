"""Disclosure containers -- a region that opens and closes over its children.

- ``CollapsibleRef``: one titled region that folds, simpler than Accordion.
  The tab owns open state while the user clicks (like Accordion) and sends a
  ``change`` on each toggle; the server can still open or close it. Its title
  is a string, or a ``header`` child (a Row of anything) in its place.
- ``SheetRef``: an edge drawer, Modal's sibling for inspectors and side
  panels. The server owns open state; the tab sends a ``change`` with
  ``value: false`` when the user dismisses it.
- ``PopoverRef``: a button that opens a small floating panel anchored to
  it, for settings that should take no room until asked for. The tab owns
  open state while the user clicks, like Collapsible.

Open vs closed is the thing each one carries, so each has a ``set()`` for
it, the way Modal does, and reading the Ref reads it back: ``nu.let(sheet,
...)`` is true while the region is open. ``on_change()`` hears each move as
``{event: "change", value: <open>}``. Every other child is open-ended composition: build
it as a slot on the Shape or as a Ref with ``parent_ref=`` this one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import Self, Unpack

from nu.lang.sentinels import UNSET
from nustd.ui.core.capabilities import Changes
from nustd.ui.core.interactions import Write

from .base import DictCollectionRef
from .flow import FLOW_CHILDREN, STACK, RowRef
from .layout import ChildLayout, StackLayout, one_of
from .named import HEADER, header_ref, part_ref


if TYPE_CHECKING:
    from nu.domains.shape import Slot
    from nu.lang import Nu
    from nu.lang.args import BoolArg, StrArg
    from nustd.ui.core import Ref, Section

    from ..leaves.input import Variant
    from ..vocab import ControlSize


__all__ = ["TRIGGER", "CollapsibleRef", "PopoverRef", "SheetRef"]


#: The child key a Popover draws inside its trigger button, in place of label and icon.
TRIGGER = "trigger"


def _open_title(open: object, title: object) -> dict[str, object]:
    """The partial chrome payload ``set()`` writes: only what was passed."""
    payload: dict[str, object] = {}
    if open is not UNSET:
        payload["open"] = open
    if title is not UNSET:
        payload["title"] = title
    return payload


class CollapsibleRef(Changes, ChildLayout, DictCollectionRef):
    """One titled region whose children fold away.

    A trigger row (chevron + title) over a body of open-ended children. The
    user toggles it in the tab, which sends ``{event: "change", value: bool}``;
    ``on_change()`` takes those, and reading the Ref gives whether it is open
    now. ``set(open=...)`` opens or closes it from
    the server. The body speaks the layers of a Column (``layout``):
    ``gap`` (3), ``padding``, ``justify``, ``align``, ``divided``, and the
    per child maps.

    ``title`` is shorthand for a header that is one line of text. For more
    (a status dot, a badge, a button) build the ``header`` child instead:
    ``coll.header`` is the Shape's ``header`` slot, or a Row there. When it
    exists it is the trigger row's content and ``title`` is not drawn. A
    click on the row's text or empty space toggles; a control in the header
    does its own thing and leaves the region as it is.
    """

    _wire_type = "Collapsible"
    _parts: ClassVar[frozenset[str]] = frozenset({HEADER})
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

    @property
    def header(self) -> Ref:
        """The trigger row's content: the Shape's ``header`` slot, or a Row there."""
        return header_ref(self)

    def set_open(self, flag: BoolArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(**_open_title(open, title)))

    def _lift(self, raw: object) -> bool:
        return bool(raw)


Side = Literal["left", "right", "top", "bottom"]
_SIDES = ("left", "right", "top", "bottom")


class SheetRef(Changes, ChildLayout, DictCollectionRef):
    """Drawer that slides in from an edge over the page, children as its body.

    Server-owned ``open`` and ``title``. For a heading that is more than a
    string, build a ``header`` child: ``sheet.header`` is the Shape's
    ``header`` slot or a Row there, drawn in the title's place with the close
    button kept beside it, and the sheet is named by its text. The sheet only
    places it, full width and free to shrink. When ``dismissible`` is true the user
    can close it (backdrop, Esc, the close button) and the tab sends
    ``{event: "change", value: false}``, which ``on_change()`` takes; reading
    the Ref gives whether it is open now. Like Modal, the sheet
    stays open until the program writes ``open=False`` back, so a program
    can hold it open (unsaved edits).

    A left or right sheet is ``width`` wide (440px unless set), a top or
    bottom one ``height`` tall (320px unless set). The body speaks the
    layers of a Column (``layout``): ``gap`` (4), ``padding``, ``justify``,
    ``align``, ``divided``, and the per child maps.
    """

    _wire_type = "Sheet"
    _parts: ClassVar[frozenset[str]] = frozenset({HEADER})
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

    @property
    def header(self) -> Ref:
        """The header line, in place of the title: the Shape's ``header`` slot, or a Row there."""
        return header_ref(self)

    def set_open(self, flag: BoolArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(open=flag))

    def set_title(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET, title: StrArg = UNSET) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(**_open_title(open, title)))

    def _lift(self, raw: object) -> bool:
        return bool(raw)


PopoverSide = Literal["top", "right", "bottom", "left"]
PopoverEdge = Literal["start", "center", "end"]
_POPOVER_SIDES = ("top", "right", "bottom", "left")
_POPOVER_EDGES = ("start", "center", "end")


class PopoverRef(Changes, ChildLayout, DictCollectionRef):
    """A button that opens a small panel floating beside it, children as its body.

    The trigger wears a button's look: ``label``, ``icon`` (a lucide name),
    ``tooltip``, ``variant`` and ``size`` read as ``ButtonRef``'s do, so an
    empty label draws a square icon button. ``title`` heads the panel. The
    panel sits on ``side`` of it, its ``edge`` (start, center, end) lined up
    with the trigger's, and takes no room in the flow: nothing around it
    moves when it opens. Escape, a click outside or the trigger close it.

    Two child keys are the popover's own places, not body. ``header`` heads
    the panel in place of ``title``; ``trigger`` is drawn inside the trigger
    button in place of ``label`` and ``icon``, in the same button look, so
    an avatar and a name open the panel as one button. ``popover.header`` and
    ``popover.trigger`` are the Shape's slots of those names, or a Row there.
    The trigger's content is display only (an avatar, text, a badge, an
    icon): a control inside a button is two targets in one. The button is
    named by ``tooltip``, else ``title``, else "Open".

    The user opens and closes it in the tab, which sends ``{event: "change",
    value: bool}``; ``on_change()`` takes those, and reading the Ref gives
    whether it is open now. ``set(open=...)`` opens or closes
    it from the server. The panel is ``width`` wide (288px unless set) and
    its body speaks the layers of a Column (``layout``): ``gap`` (3),
    ``padding``, ``justify``, ``align``, ``divided``, and the per child maps.
    """

    _wire_type = "Popover"
    _parts: ClassVar[frozenset[str]] = frozenset({HEADER, TRIGGER})
    _layout: ClassVar[frozenset[str]] = STACK
    _children: ClassVar[tuple[str, ...]] = FLOW_CHILDREN

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        *,
        label: str = "",
        icon: str = "",
        tooltip: str = "",
        title: str = "",
        variant: Variant = "ghost",
        size: ControlSize = "sm",
        side: PopoverSide = "bottom",
        edge: PopoverEdge = "end",
        open: bool = False,
        **layout: Unpack[StackLayout],
    ) -> Self:
        return super().slot(
            item,
            label=label,
            icon=icon,
            tooltip=tooltip,
            title=title,
            variant=variant,
            size=size,
            side=one_of("PopoverRef", "side", side, _POPOVER_SIDES),
            edge=one_of("PopoverRef", "edge", edge, _POPOVER_EDGES),
            open=bool(open),
            **cls._laid_out(layout),
        )

    @property
    def header(self) -> Ref:
        """The panel's header, in place of the title: the Shape's ``header`` slot, or a Row there."""
        return header_ref(self)

    @property
    def trigger(self) -> Ref:
        """The trigger button's content: the Shape's ``trigger`` slot, or a Row there."""
        return part_ref(self, TRIGGER, RowRef.slot(gap=2))

    def set_open(self, flag: BoolArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(open=flag))

    def set_label(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(label=text))

    def set_tooltip(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(tooltip=text))

    def set_title(self, text: StrArg) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(title=text))

    def set(self, open: BoolArg = UNSET) -> Nu:
        from nu.forms import Dict

        return Write(self, Dict.of(**({} if open is UNSET else {"open": open})))

    def _lift(self, raw: object) -> bool:
        return bool(raw)
