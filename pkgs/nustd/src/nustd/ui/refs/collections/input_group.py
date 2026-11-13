"""``InputGroupRef`` -- a field and the buttons that act on it, on one line.

The line every "type, then press" form has: a search box and Search, a chat
box and Send, a name and Create. A Row can draw it, but only with the app
saying ``align="end"`` and ``grow={"field": 1}`` every time. The group knows
what it holds, so it says it once: the children with no width of their own
(an input, a select, a date picker) take the width, the rest (a button, a
toggle) keep theirs, and all of them sit on the line's bottom edge, so a
labelled field's box lines up with its buttons.

A container, not a prop on ``InputRef``: the buttons are refs of their own
with their own events, and a leaf holds no children (``refs`` docstring).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import Self, Unpack

from .base import DictCollectionRef
from .layout import SIZE, SizeLayout


if TYPE_CHECKING:
    from nu.domains.shape import Slot
    from nustd.ui.core import Ref, Section


__all__ = ["InputGroupLayout", "InputGroupRef"]


class InputGroupLayout(SizeLayout, total=False):
    """An InputGroup's layout: the size layer, and the gap between children."""

    gap: int


class InputGroupRef(DictCollectionRef):
    """A field and the buttons that act on it, on one line.

    ::

        class Say(InputGroup):
            text = InputRef.slot(placeholder="Say something")
            send = ButtonRef.slot(label="Send", icon="send")

    Fill children (inputs) share the width, the rest keep their own, every
    child sits on the bottom edge. Children draw in order, like a Row. Layout
    (``layout``): the size layer and ``gap`` (2, 8px). No per child maps: the
    group sizes each child by its kind.

    In a Form's values it nests like any container (``{"say": {"text":
    ...}}``). For a label, help or an error over the whole line, put the
    group in a ``Field``; a Field inside the group would push the field's box
    above the buttons with its help line.
    """

    _wire_type = "InputGroup"
    _layout: ClassVar[frozenset[str]] = SIZE | {"gap"}

    @classmethod
    def slot(
        cls,
        item: type[Section] | type[Ref] | Slot | None = None,
        /,
        **layout: Unpack[InputGroupLayout],
    ) -> Self:
        return super().slot(item, **cls._laid_out(layout))
